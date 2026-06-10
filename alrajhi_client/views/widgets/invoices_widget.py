# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                             QTabWidget, QDateEdit, QComboBox, QLabel, QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt, QDate
from decimal import Decimal
from core.services.invoice_service import invoice_service
from core.services.catalog_service import catalog_service
from currency import currency
from views.custom_table_view import CustomTableView
from models.table_models import GenericTableModel
from views.dialogs.invoice_dialog import InvoiceDialog
from utils import show_toast

class InvoicesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.sales_page = 0
        self.purchases_page = 0
        self.page_size = 50

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        self.tabs = QTabWidget()
        self.sales_tab = QWidget()
        self.purchases_tab = QWidget()
        self.setup_sales_tab()
        self.setup_purchases_tab()
        self.tabs.addTab(self.sales_tab, "💰 فواتير البيع")
        self.tabs.addTab(self.purchases_tab, "📦 فواتير الشراء")
        layout.addWidget(self.tabs)

        self.refresh_all()

    def setup_sales_tab(self):
        layout = QVBoxLayout(self.sales_tab)
        # شريط الفلترة
        filter_layout = QHBoxLayout()
        self.sales_search = QLineEdit()
        self.sales_search.setPlaceholderText("بحث...")
        self.sales_search.textChanged.connect(lambda: self.refresh_tab('sale', reset_page=True))
        filter_layout.addWidget(self.sales_search)

        self.sales_start_date = QDateEdit()
        self.sales_start_date.setDate(QDate.currentDate().addDays(-30))
        self.sales_start_date.setCalendarPopup(True)
        self.sales_start_date.dateChanged.connect(lambda: self.refresh_tab('sale', reset_page=True))
        filter_layout.addWidget(QLabel("من:"))
        filter_layout.addWidget(self.sales_start_date)

        self.sales_end_date = QDateEdit()
        self.sales_end_date.setDate(QDate.currentDate())
        self.sales_end_date.setCalendarPopup(True)
        self.sales_end_date.dateChanged.connect(lambda: self.refresh_tab('sale', reset_page=True))
        filter_layout.addWidget(QLabel("إلى:"))
        filter_layout.addWidget(self.sales_end_date)

        self.sales_customer_combo = QComboBox()
        self.sales_customer_combo.addItem("الكل", None)
        self.load_customers()
        self.sales_customer_combo.currentIndexChanged.connect(lambda: self.refresh_tab('sale', reset_page=True))
        filter_layout.addWidget(QLabel("العميل:"))
        filter_layout.addWidget(self.sales_customer_combo)

        add_sale_btn = QPushButton("➕ فاتورة بيع جديدة")
        add_sale_btn.clicked.connect(lambda: self.create_invoice('sale'))
        filter_layout.addWidget(add_sale_btn)
        layout.addLayout(filter_layout)

        self.sales_table = CustomTableView()
        self.sales_table.setSelectionBehavior(CustomTableView.SelectRows)
        self.sales_table.doubleClicked.connect(lambda idx: self.edit_invoice('sale', idx))
        layout.addWidget(self.sales_table)

        # شريط التنقل
        pagination = QHBoxLayout()
        self.sales_prev = QPushButton("السابق")
        self.sales_prev.clicked.connect(lambda: self.prev_page('sale'))
        self.sales_next = QPushButton("التالي")
        self.sales_next.clicked.connect(lambda: self.next_page('sale'))
        self.sales_page_label = QLabel()
        pagination.addWidget(self.sales_prev)
        pagination.addWidget(self.sales_page_label)
        pagination.addWidget(self.sales_next)
        pagination.addStretch()
        layout.addLayout(pagination)

    def setup_purchases_tab(self):
        layout = QVBoxLayout(self.purchases_tab)
        filter_layout = QHBoxLayout()
        self.purchases_search = QLineEdit()
        self.purchases_search.setPlaceholderText("بحث...")
        self.purchases_search.textChanged.connect(lambda: self.refresh_tab('purchase', reset_page=True))
        filter_layout.addWidget(self.purchases_search)

        self.purchases_start_date = QDateEdit()
        self.purchases_start_date.setDate(QDate.currentDate().addDays(-30))
        self.purchases_start_date.setCalendarPopup(True)
        self.purchases_start_date.dateChanged.connect(lambda: self.refresh_tab('purchase', reset_page=True))
        filter_layout.addWidget(QLabel("من:"))
        filter_layout.addWidget(self.purchases_start_date)

        self.purchases_end_date = QDateEdit()
        self.purchases_end_date.setDate(QDate.currentDate())
        self.purchases_end_date.setCalendarPopup(True)
        self.purchases_end_date.dateChanged.connect(lambda: self.refresh_tab('purchase', reset_page=True))
        filter_layout.addWidget(QLabel("إلى:"))
        filter_layout.addWidget(self.purchases_end_date)

        self.purchases_supplier_combo = QComboBox()
        self.purchases_supplier_combo.addItem("الكل", None)
        self.load_suppliers()
        self.purchases_supplier_combo.currentIndexChanged.connect(lambda: self.refresh_tab('purchase', reset_page=True))
        filter_layout.addWidget(QLabel("المورد:"))
        filter_layout.addWidget(self.purchases_supplier_combo)

        add_purchase_btn = QPushButton("➕ فاتورة شراء جديدة")
        add_purchase_btn.clicked.connect(lambda: self.create_invoice('purchase'))
        filter_layout.addWidget(add_purchase_btn)
        layout.addLayout(filter_layout)

        self.purchases_table = CustomTableView()
        self.purchases_table.setSelectionBehavior(CustomTableView.SelectRows)
        self.purchases_table.doubleClicked.connect(lambda idx: self.edit_invoice('purchase', idx))
        layout.addWidget(self.purchases_table)

        pagination = QHBoxLayout()
        self.purchases_prev = QPushButton("السابق")
        self.purchases_prev.clicked.connect(lambda: self.prev_page('purchase'))
        self.purchases_next = QPushButton("التالي")
        self.purchases_next.clicked.connect(lambda: self.next_page('purchase'))
        self.purchases_page_label = QLabel()
        pagination.addWidget(self.purchases_prev)
        pagination.addWidget(self.purchases_page_label)
        pagination.addWidget(self.purchases_next)
        pagination.addStretch()
        layout.addLayout(pagination)

    def load_customers(self):
        customers = catalog_service.customers(limit=1000)  # جلب أول 1000 عميل فقط للقائمة
        for c in customers:
            self.sales_customer_combo.addItem(c.get('name', ''), c.get('id'))

    def load_suppliers(self):
        suppliers = catalog_service.suppliers(limit=1000)
        for s in suppliers:
            self.purchases_supplier_combo.addItem(s.get('name', ''), s.get('id'))

    def refresh_all(self):
        self.refresh_tab('sale', reset_page=True)
        self.refresh_tab('purchase', reset_page=True)

    def refresh_tab(self, inv_type, reset_page=False):
        if inv_type == 'sale':
            if reset_page:
                self.sales_page = 0
            search = self.sales_search.text().strip() or None
            start_date = self.sales_start_date.date().toString("yyyy-MM-dd")
            end_date = self.sales_end_date.date().toString("yyyy-MM-dd")
            customer_id = self.sales_customer_combo.currentData()
            invoices, total = invoice_service.list_invoices(
                search=search, inv_type='sale', start_date=start_date, end_date=end_date,
                customer_id=customer_id, limit=self.page_size, offset=self.sales_page * self.page_size
            )
            data = []
            for inv in invoices:
                remaining = Decimal(str(inv.get('total', 0))) - Decimal(str(inv.get('paid', 0)))
                data.append({
                    'id': inv['id'],
                    'reference': inv.get('reference', ''),
                    'date': inv.get('date', ''),
                    'customer': inv.get('customer_name', 'نقدي'),
                    'total': currency.format_amount(currency.convert(inv.get('total', 0), 'USD', currency.get_display_currency())),
                    'paid': currency.format_amount(currency.convert(inv.get('paid', 0), 'USD', currency.get_display_currency())),
                    'remaining': currency.format_amount(currency.convert(remaining, 'USD', currency.get_display_currency()))
                })
            headers = ['reference', 'date', 'customer', 'total', 'paid', 'remaining']
            display_headers = ['المرجع', 'التاريخ', 'العميل', 'الإجمالي', 'المدفوع', 'المتبقي']
            model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
            self.sales_table.setModel(model)
            # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض.
            self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.sales_table.refresh_style()
            self.sales_invoices = invoices
            total_pages = (total + self.page_size - 1) // self.page_size
            self.sales_page_label.setText(f"الصفحة {self.sales_page + 1} من {total_pages}")
            self.sales_prev.setEnabled(self.sales_page > 0)
            self.sales_next.setEnabled(self.sales_page + 1 < total_pages)
        else:
            if reset_page:
                self.purchases_page = 0
            search = self.purchases_search.text().strip() or None
            start_date = self.purchases_start_date.date().toString("yyyy-MM-dd")
            end_date = self.purchases_end_date.date().toString("yyyy-MM-dd")
            supplier_id = self.purchases_supplier_combo.currentData()
            invoices, total = invoice_service.list_invoices(
                search=search, inv_type='purchase', start_date=start_date, end_date=end_date,
                supplier_id=supplier_id, limit=self.page_size, offset=self.purchases_page * self.page_size
            )
            data = []
            for inv in invoices:
                remaining = Decimal(str(inv.get('total', 0))) - Decimal(str(inv.get('paid', 0)))
                data.append({
                    'id': inv['id'],
                    'reference': inv.get('reference', ''),
                    'date': inv.get('date', ''),
                    'supplier': inv.get('supplier_name', 'نقدي'),
                    'total': currency.format_amount(currency.convert(inv.get('total', 0), 'USD', currency.get_display_currency())),
                    'paid': currency.format_amount(currency.convert(inv.get('paid', 0), 'USD', currency.get_display_currency())),
                    'remaining': currency.format_amount(currency.convert(remaining, 'USD', currency.get_display_currency()))
                })
            headers = ['reference', 'date', 'supplier', 'total', 'paid', 'remaining']
            display_headers = ['المرجع', 'التاريخ', 'المورد', 'الإجمالي', 'المدفوع', 'المتبقي']
            model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
            self.purchases_table.setModel(model)
            # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض.
            self.purchases_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.purchases_table.refresh_style()
            self.purchases_invoices = invoices
            total_pages = (total + self.page_size - 1) // self.page_size
            self.purchases_page_label.setText(f"الصفحة {self.purchases_page + 1} من {total_pages}")
            self.purchases_prev.setEnabled(self.purchases_page > 0)
            self.purchases_next.setEnabled(self.purchases_page + 1 < total_pages)

    def create_invoice(self, inv_type):
        dialog = InvoiceDialog(inv_type, self)
        if dialog.exec():
            self.refresh_all()

    def edit_invoice(self, inv_type, index):
        row = index.row()
        if inv_type == 'sale':
            inv_id = self.sales_table.model().get_id(row)
        else:
            inv_id = self.purchases_table.model().get_id(row)
        if inv_id:
            dialog = InvoiceDialog(inv_type, self, invoice_id=inv_id)
            if dialog.exec():
                self.refresh_all()

    def prev_page(self, inv_type):
        if inv_type == 'sale' and self.sales_page > 0:
            self.sales_page -= 1
            self.refresh_tab('sale')
        elif inv_type == 'purchase' and self.purchases_page > 0:
            self.purchases_page -= 1
            self.refresh_tab('purchase')

    def next_page(self, inv_type):
        if inv_type == 'sale':
            self.sales_page += 1
            self.refresh_tab('sale')
        else:
            self.purchases_page += 1
            self.refresh_tab('purchase')


