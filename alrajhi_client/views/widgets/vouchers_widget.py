# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                             QDateEdit, QComboBox, QLabel, QHeaderView, QMessageBox, QFormLayout,
                             QDoubleSpinBox, QDialog, QDialogButtonBox, QMenu)
from PyQt5.QtCore import Qt, QDate
from decimal import Decimal
from core.services.voucher_service import voucher_service
from core.services.catalog_service import catalog_service
from core.services.invoice_service import invoice_service
from core.services.cashbox_service import cashbox_service
from currency import currency
from views.custom_table_view import CustomTableView
from models.table_models import GenericTableModel
from utils import show_toast
from offline_read import is_offline_read_error, notify_offline_read
from offline_read import is_offline_read_error, notify_offline_read
from views.widgets.modern_ui import apply_modern_widget, apply_modern_dialog

class VouchersWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.current_page = 0
        self.page_size = 50
        self.total_count = 0

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        top_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("بحث عن سند...")
        self.search_edit.textChanged.connect(self.refresh)
        top_layout.addWidget(self.search_edit)

        self.type_filter = QComboBox()
        self.type_filter.addItems(["الكل", "قبض", "دفع", "مصروف"])
        self.type_filter.currentIndexChanged.connect(self.refresh)
        top_layout.addWidget(QLabel("النوع:"))
        top_layout.addWidget(self.type_filter)

        self.add_btn = QPushButton("➕ إضافة سند")
        self.add_btn.setObjectName("primary")
        self.add_btn.clicked.connect(self.add_voucher)
        top_layout.addWidget(self.add_btn)

        self.print_btn = QPushButton("🖨️ طباعة")
        print_menu = QMenu(self.print_btn)
        print_menu.addAction("معاينة داخل البرنامج", lambda: self.print_selected('preview'))
        print_menu.addAction("فتح HTML في المتصفح", lambda: self.print_selected('browser'))
        print_menu.addAction("طباعة مباشرة", lambda: self.print_selected('direct'))
        print_menu.addAction("تصدير PDF", lambda: self.print_selected('pdf'))
        self.print_btn.setMenu(print_menu)
        top_layout.addWidget(self.print_btn)

        layout.addLayout(top_layout)

        self.table = CustomTableView()
        self.table.setSelectionBehavior(CustomTableView.SelectRows)
        self.table.doubleClicked.connect(self.edit_voucher)
        layout.addWidget(self.table)

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

        apply_modern_widget(self, '🧾 السندات', 'إدارة سندات القبض والصرف والبحث السريع')
        self.refresh()

    def refresh(self):
        filter_type = self.type_filter.currentText()
        vtype = None
        if filter_type == "قبض":
            vtype = 'receipt'
        elif filter_type == "دفع":
            vtype = 'payment'
        elif filter_type == "مصروف":
            vtype = 'expense'
        search = self.search_edit.text().strip().lower() or None
        offset = self.current_page * self.page_size
        try:
            vouchers, self.total_count = voucher_service.list_vouchers(search=search, vtype=vtype, limit=self.page_size, offset=offset)
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, 'السندات')
                return
            raise

        data = []
        display_curr = currency.get_display_currency()
        for v in vouchers:
            amount_display = currency.convert(Decimal(str(v['amount'])), 'USD', display_curr)
            type_text = "قبض" if v['type'] == 'receipt' else "دفع" if v['type'] == 'payment' else "مصروف"
            party = voucher_service.party_name(v)
            data.append({
                'id': v['id'],
                'date': v['date'],
                'type': type_text,
                'party': party,
                'amount': currency.format_amount(amount_display),
                'account': v.get('cashbox_name') or v.get('bank_name') or '',
                'description': v.get('description', '')
            })
        headers = ['date', 'type', 'party', 'amount', 'account', 'description']
        display_headers = ['التاريخ', 'النوع', 'الجهة', 'المبلغ', 'الحساب', 'الوصف']
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

    def _selected_id(self):
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not rows or not hasattr(self, 'model'):
            return None
        return self.model.get_id(rows[0].row())

    def print_selected(self, mode='preview'):
        vid = self._selected_id()
        if not vid:
            QMessageBox.information(self, "طباعة", "اختر سنداً أولاً")
            return
        voucher = voucher_service.get(vid)
        if not voucher:
            QMessageBox.warning(self, "طباعة", "تعذر تحميل بيانات السند")
            return
        voucher = dict(voucher)
        voucher['party_name'] = voucher_service.party_name(voucher)
        from printing.printing_service import printing_service
        if mode == 'browser':
            printing_service.voucher_browser(voucher, self)
        elif mode == 'direct':
            printing_service.voucher_print(voucher, self)
        elif mode == 'pdf':
            printing_service.voucher_pdf(voucher, self)
        else:
            printing_service.voucher_preview(voucher, self)

    def add_voucher(self):
        dialog = VoucherDialog(self)
        if dialog.exec():
            self.refresh()

    def edit_voucher(self, index):
        row = index.row()
        vid = self.model.get_id(row)
        if vid:
            voucher = voucher_service.get(vid)
            if voucher:
                dialog = VoucherDialog(self, voucher)
                if dialog.exec():
                    self.refresh()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh()

    def next_page(self):
        self.current_page += 1
        self.refresh()

class VoucherDialog(QDialog):
    # ... (نفس الكود السابق مع دعم التعديل) ...
    # للحفاظ على الطول، سيتم تضمين نفس الكود من الإصدار السابق.
    def __init__(self, parent=None, voucher=None):
        super().__init__(parent)
        self.voucher = voucher
        self.is_edit = voucher is not None
        self.setWindowTitle("تعديل سند" if self.is_edit else "إضافة سند جديد")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(450, 500)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["قبض", "دفع", "مصروف"])
        form.addRow("النوع:", self.type_combo)

        self.customer_combo = QComboBox()
        self.customer_combo.addItem("بدون عميل", None)
        try:
            customers = catalog_service.customers(limit=1000)
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, 'قائمة العملاء للسندات')
                customers = []
            else:
                raise
        for c in customers:
            self.customer_combo.addItem(c.get('name', ''), c.get('id'))
        form.addRow("العميل:", self.customer_combo)

        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("بدون مورد", None)
        try:
            suppliers = catalog_service.suppliers(limit=1000)
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, 'قائمة الموردين للسندات')
                suppliers = []
            else:
                raise
        for s in suppliers:
            self.supplier_combo.addItem(s.get('name', ''), s.get('id'))
        form.addRow("المورد:", self.supplier_combo)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 99999999)
        self.amount_spin.setDecimals(2)
        form.addRow("المبلغ:", self.amount_spin)

        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItem("نقدي", 'cash')
        self.payment_method_combo.addItem("بنك", 'bank')
        form.addRow("طريقة الدفع:", self.payment_method_combo)

        self.cashbox_combo = QComboBox()
        for c in cashbox_service.cashboxes():
            label = f"{c.get('branch_name','')} - {c.get('name','')}"
            self.cashbox_combo.addItem(label, c.get('id'))
        form.addRow("الصندوق:", self.cashbox_combo)

        self.bank_combo = QComboBox()
        self.bank_combo.addItem("اختر حساباً بنكياً", None)
        for b in cashbox_service.bank_accounts():
            label = f"{b.get('branch_name','')} - {b.get('bank_name','')} {b.get('account_name') or ''}"
            self.bank_combo.addItem(label, b.get('id'))
        form.addRow("الحساب البنكي:", self.bank_combo)

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("التاريخ:", self.date_edit)

        self.desc_edit = QLineEdit()
        form.addRow("الوصف:", self.desc_edit)

        self.ref_edit = QLineEdit()
        form.addRow("المرجع:", self.ref_edit)

        self.invoice_combo = QComboBox()
        self.invoice_combo.addItem("بدون فاتورة", None)
        form.addRow("الفاتورة:", self.invoice_combo)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.save)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        apply_modern_dialog(self, 'سند قبض/صرف')

        def update_visibility():
            typ = self.type_combo.currentText()
            is_cash = typ in ("قبض", "دفع")
            self.customer_combo.setVisible(typ == "قبض")
            self.supplier_combo.setVisible(typ == "دفع")
            self.invoice_combo.setVisible(is_cash)
            self.update_invoice_list()
        self.type_combo.currentTextChanged.connect(update_visibility)
        self.customer_combo.currentIndexChanged.connect(self.update_invoice_list)
        self.supplier_combo.currentIndexChanged.connect(self.update_invoice_list)
        self.payment_method_combo.currentIndexChanged.connect(self.update_payment_visibility)

        if self.is_edit:
            self.load_voucher_data()
        update_visibility()
        self.update_payment_visibility()

    def update_payment_visibility(self):
        is_bank = self.payment_method_combo.currentData() == 'bank'
        self.bank_combo.setVisible(is_bank)
        self.cashbox_combo.setVisible(not is_bank)

    def load_voucher_data(self):
        v = self.voucher
        type_map = {"receipt": "قبض", "payment": "دفع", "expense": "مصروف"}
        self.type_combo.setCurrentText(type_map.get(v['type'], "مصروف"))
        if v.get('customer_id'):
            idx = self.customer_combo.findData(v['customer_id'])
            if idx >= 0:
                self.customer_combo.setCurrentIndex(idx)
        if v.get('supplier_id'):
            idx = self.supplier_combo.findData(v['supplier_id'])
            if idx >= 0:
                self.supplier_combo.setCurrentIndex(idx)
        amount_display = currency.convert(Decimal(str(v['amount'])), 'USD', currency.get_display_currency())
        self.amount_spin.setValue(float(amount_display))
        self.date_edit.setDate(QDate.fromString(v['date'], "yyyy-MM-dd"))
        self.desc_edit.setText(v.get('description', ''))
        self.ref_edit.setText(v.get('reference', ''))
        if v.get('payment_method') == 'bank':
            self.payment_method_combo.setCurrentIndex(self.payment_method_combo.findData('bank'))
        else:
            self.payment_method_combo.setCurrentIndex(self.payment_method_combo.findData('cash'))
        if v.get('cashbox_id'):
            idx = self.cashbox_combo.findData(v.get('cashbox_id'))
            if idx >= 0:
                self.cashbox_combo.setCurrentIndex(idx)
        if v.get('bank_account_id'):
            idx = self.bank_combo.findData(v.get('bank_account_id'))
            if idx >= 0:
                self.bank_combo.setCurrentIndex(idx)
        self.update_payment_visibility()
        if v.get('invoice_id'):
            self.update_invoice_list()
            idx = self.invoice_combo.findData(v['invoice_id'])
            if idx >= 0:
                self.invoice_combo.setCurrentIndex(idx)

    def update_invoice_list(self):
        typ = self.type_combo.currentText()
        entity_id = None
        if typ == "قبض":
            entity_id = self.customer_combo.currentData()
        elif typ == "دفع":
            entity_id = self.supplier_combo.currentData()
        if not entity_id:
            self.invoice_combo.clear()
            self.invoice_combo.addItem("بدون فاتورة", None)
            return
        # جلب الفواتير غير المسددة بالكامل (محدودة للعرض)
        invoices = invoice_service.unpaid_invoices(
            inv_type='sale' if typ == "قبض" else 'purchase',
            customer_id=entity_id if typ == "قبض" else None,
            supplier_id=entity_id if typ == "دفع" else None,
            limit=100
        )
        self.invoice_combo.clear()
        self.invoice_combo.addItem("بدون فاتورة", None)
        for inv in invoices:
            remaining = Decimal(str(inv.get('total', 0))) - Decimal(str(inv.get('paid', 0)))
            if remaining > 0:
                self.invoice_combo.addItem(f"{inv['reference']} - متبقي: {currency.format_amount(currency.convert(remaining, 'USD', currency.get_display_currency()))}", inv['id'])

    def save(self):
        typ = self.type_combo.currentText()
        if typ == "قبض" and not self.customer_combo.currentData():
            show_toast("اختر عميلاً", "error", self)
            return
        if typ == "دفع" and not self.supplier_combo.currentData():
            show_toast("اختر مورداً", "error", self)
            return
        if self.payment_method_combo.currentData() == 'cash' and not self.cashbox_combo.currentData():
            show_toast("اختر صندوقاً", "error", self)
            return
        if self.payment_method_combo.currentData() == 'bank' and not self.bank_combo.currentData():
            show_toast("اختر حساباً بنكياً", "error", self)
            return
        amount_display = self.amount_spin.value()
        if amount_display <= 0:
            show_toast("المبلغ يجب أن يكون أكبر من صفر", "error", self)
            return
        amount_usd = currency.convert(Decimal(str(amount_display)), currency.get_display_currency(), 'USD')
        data = {
            'type': 'receipt' if typ == "قبض" else ('payment' if typ == "دفع" else 'expense'),
            'amount': amount_usd,
            'date': self.date_edit.date().toString("yyyy-MM-dd"),
            'description': self.desc_edit.text().strip(),
            'reference': self.ref_edit.text().strip(),
            'customer_id': self.customer_combo.currentData() if typ == "قبض" else None,
            'supplier_id': self.supplier_combo.currentData() if typ == "دفع" else None,
            'invoice_id': self.invoice_combo.currentData() or None,
            'exchange_rate_to_usd': float(currency.get_current_rate(currency.get_display_currency())),
            'original_currency': currency.get_display_currency(),
            'payment_method': self.payment_method_combo.currentData(),
            'cashbox_id': self.cashbox_combo.currentData() if self.payment_method_combo.currentData() == 'cash' else None,
            'bank_account_id': self.bank_combo.currentData() if self.payment_method_combo.currentData() == 'bank' else None
        }
        try:
            if self.is_edit:
                voucher_service.update(self.voucher['id'], data)
                show_toast("تم تعديل السند", "success", self)
            else:
                voucher_service.add(data)
                show_toast("تمت الإضافة", "success", self)
            self.accept()
        except Exception as e:
            show_toast(str(e), "error", self)


