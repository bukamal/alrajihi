# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                             QLabel, QComboBox, QHeaderView, QMessageBox, QDialog, QFormLayout)
from PyQt5.QtCore import Qt
from decimal import Decimal
from core.services.entity_service import entity_service
from currency import currency
from views.custom_table_view import CustomTableView
from models.table_models import GenericTableModel
from views.centered_dialog import CenteredDialog
from views.dialogs.add_entity_dialog import AddEntityDialog
from utils import show_toast

class CustomersWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.current_page = 0
        self.page_size = 50
        self.total_count = 0

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # شريط البحث والفلترة
        top_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("بحث عن عميل...")
        self.search_edit.textChanged.connect(self.refresh)
        top_layout.addWidget(self.search_edit)

        self.balance_filter = QComboBox()
        self.balance_filter.addItems(["الكل", "رصيد موجب", "رصيد سالب", "رصيد صفر"])
        self.balance_filter.currentIndexChanged.connect(self.refresh)
        top_layout.addWidget(QLabel("فلتر الرصيد:"))
        top_layout.addWidget(self.balance_filter)

        self.add_btn = QPushButton("➕ إضافة عميل")
        self.add_btn.setObjectName("primary")
        self.add_btn.clicked.connect(self.add_customer)
        top_layout.addWidget(self.add_btn)

        layout.addLayout(top_layout)

        # الجدول
        self.table = CustomTableView()
        self.table.setSelectionBehavior(CustomTableView.SelectRows)
        self.table.doubleClicked.connect(self.edit_customer)
        layout.addWidget(self.table)

        # شريط التنقل بين الصفحات
        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton("السابق")
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn = QPushButton("التالي")
        self.next_btn.clicked.connect(self.next_page)
        self.page_label = QLabel()
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)

        self.refresh()

    def refresh(self):
        search = self.search_edit.text().strip() or None
        offset = self.current_page * self.page_size
        customers, self.total_count = entity_service.customers(search=search, limit=self.page_size, offset=offset)
        display_curr = currency.get_display_currency()
        data = []
        for c in customers:
            balance_display = currency.convert(Decimal(str(c.get('balance', 0))), 'USD', display_curr)
            # تطبيق فلتر الرصيد (جانب العميل)
            filter_idx = self.balance_filter.currentIndex()
            if filter_idx == 1 and balance_display <= 0:
                continue
            if filter_idx == 2 and balance_display >= 0:
                continue
            if filter_idx == 3 and balance_display != 0:
                continue
            data.append({
                'id': c['id'],
                'name': c.get('name', ''),
                'phone': c.get('phone', ''),
                'address': c.get('address', ''),
                'balance': currency.format_amount(balance_display)
            })
        headers = ['name', 'phone', 'address', 'balance']
        display_headers = ['الاسم', 'الهاتف', 'العنوان', 'الرصيد']
        self.model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
        self.table.setModel(self.model)
        # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض؛ لا نخفي العمود الأول الحقيقي.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.refresh_style()

        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        self.page_label.setText(f"الصفحة {self.current_page + 1} من {total_pages}")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page + 1 < total_pages)

    def add_customer(self):
        dialog = AddEntityDialog(self, 'sale')
        if dialog.exec():
            self.refresh()

    def edit_customer(self, index):
        row = index.row()
        cust_id = self.model.get_id(row)
        if not cust_id:
            return
        cust = entity_service.customer_by_id(cust_id)
        if not cust:
            return
        dialog = CenteredDialog(self)
        dialog.setWindowTitle("تعديل عميل")
        dialog.resize(400, 300)
        layout = QFormLayout(dialog.content_widget)
        name_edit = QLineEdit()
        name_edit.setText(cust.get('name', ''))
        phone_edit = QLineEdit()
        phone_edit.setText(cust.get('phone', ''))
        address_edit = QLineEdit()
        address_edit.setText(cust.get('address', ''))
        layout.addRow("الاسم:", name_edit)
        layout.addRow("الهاتف:", phone_edit)
        layout.addRow("العنوان:", address_edit)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("حفظ")
        cancel_btn = QPushButton("إلغاء")
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        def save():
            try:
                entity_service.update_customer(cust_id, name_edit.text().strip(), phone_edit.text().strip(), address_edit.text().strip())
                show_toast("تم التحديث", "success", dialog)
                dialog.accept()
                self.refresh()
            except Exception as e:
                show_toast(str(e), "error", dialog)
        save_btn.clicked.connect(save)
        cancel_btn.clicked.connect(dialog.reject)
        dialog.exec()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh()

    def next_page(self):
        self.current_page += 1
        self.refresh()


