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
from i18n import translate as tr, qt_layout_direction

class VouchersWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        self.current_page = 0
        self.page_size = 50
        self.total_count = 0

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        top_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(tr("search_voucher"))
        self.search_edit.textChanged.connect(self.refresh)
        top_layout.addWidget(self.search_edit)

        self.type_filter = QComboBox()
        
        self.type_filter.addItem(tr("all"), "all")
        self.type_filter.addItem(tr("receipt"), "receipt")
        self.type_filter.addItem(tr("payment"), "payment")
        self.type_filter.addItem(tr("expense"), "expense")
        self.type_filter.currentIndexChanged.connect(self.refresh)
        top_layout.addWidget(QLabel(tr("type") + ":"))
        top_layout.addWidget(self.type_filter)

        self.add_btn = QPushButton(tr("add_voucher"))
        self.add_btn.setObjectName("primary")
        self.add_btn.clicked.connect(self.add_voucher)
        top_layout.addWidget(self.add_btn)

        self.delete_btn = QPushButton(tr("delete_voucher"))
        self.delete_btn.setObjectName("danger")
        self.delete_btn.clicked.connect(self.delete_selected_voucher)
        top_layout.addWidget(self.delete_btn)

        self.print_btn = QPushButton(tr("print_button"))
        print_menu = QMenu(self.print_btn)
        print_menu.addAction(tr("preview_inside_app"), lambda: self.print_selected('preview'))
        print_menu.addAction(tr("open_html_browser"), lambda: self.print_selected('browser'))
        print_menu.addAction(tr("direct_print"), lambda: self.print_selected('direct'))
        print_menu.addAction(tr("export_pdf"), lambda: self.print_selected('pdf'))
        self.print_btn.setMenu(print_menu)
        top_layout.addWidget(self.print_btn)

        layout.addLayout(top_layout)

        self.table = CustomTableView()
        self.table.setSelectionBehavior(CustomTableView.SelectRows)
        self.table.doubleClicked.connect(self.edit_voucher)
        layout.addWidget(self.table)

        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton(tr("previous"))
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn = QPushButton(tr("next"))
        self.next_btn.clicked.connect(self.next_page)
        self.page_label = QLabel()
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)

        apply_modern_widget(self, tr('vouchers_title'), tr('vouchers_subtitle'))
        self.refresh()

    def set_global_filter(self, text: str):
        text = text or ''
        field = getattr(self, 'search_edit', None)
        if field is not None and field.text() != text:
            field.setText(text)
        elif hasattr(self, 'refresh'):
            self.refresh()


    def refresh(self):
        filter_type = self.type_filter.currentData() or "all"
        vtype = None
        if filter_type == "receipt":
            vtype = 'receipt'
        elif filter_type == "payment":
            vtype = 'payment'
        elif filter_type == "expense":
            vtype = 'expense'
        search = self.search_edit.text().strip().lower() or None
        offset = self.current_page * self.page_size
        try:
            vouchers, self.total_count = voucher_service.list_vouchers(search=search, vtype=vtype, limit=self.page_size, offset=offset)
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, tr('vouchers_title'))
                return
            raise

        data = []
        display_curr = currency.get_display_currency()
        for v in vouchers:
            amount_display = currency.convert(Decimal(str(v['amount'])), 'USD', display_curr)
            type_text = tr("receipt") if v['type'] == 'receipt' else tr("payment") if v['type'] == 'payment' else tr("expense")
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
        display_headers = [tr('date'), tr('type'), tr('party'), tr('amount'), tr('account'), tr('description')]
        self.model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
        self.table.setModel(self.model)
        # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض؛ لا نخفي العمود الأول الحقيقي.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.refresh_style()

        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        self.page_label.setText(tr("page_of", page=self.current_page + 1, pages=total_pages))
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page + 1 < total_pages)

    def _selected_id(self):
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not rows or not hasattr(self, 'model'):
            return None
        return self.model.get_id(rows[0].row())

    def delete_selected_voucher(self):
        vid = self._selected_id()
        if not vid:
            QMessageBox.information(self, tr("delete_voucher"), tr("select_voucher_first"))
            return
        voucher = voucher_service.get(vid)
        if not voucher:
            QMessageBox.warning(self, tr("delete_voucher"), tr("voucher_load_failed"))
            return
        amount = voucher.get('amount') or ''
        reply = QMessageBox.question(
            self,
            tr("delete_voucher"),
            tr("delete_voucher_confirm", id=vid, amount=amount),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            voucher_service.delete(vid)
            show_toast(tr("voucher_deleted"), "success", self)
            self.refresh()
        except Exception as exc:
            show_toast(str(exc), "error", self)

    def print_selected(self, mode='preview'):
        vid = self._selected_id()
        if not vid:
            QMessageBox.information(self, tr("print_button"), tr("select_voucher_first"))
            return
        voucher = voucher_service.get(vid)
        if not voucher:
            QMessageBox.warning(self, tr("print_button"), tr("voucher_load_failed"))
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
        self.setWindowTitle(tr("edit_voucher") if self.is_edit else tr("new_voucher"))
        self.setLayoutDirection(qt_layout_direction())
        self.resize(450, 500)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItem(tr("receipt"), "receipt")
        self.type_combo.addItem(tr("payment"), "payment")
        self.type_combo.addItem(tr("expense"), "expense")
        form.addRow(tr("type") + ":", self.type_combo)

        self.customer_combo = QComboBox()
        self.customer_combo.addItem(tr("no_customer"), None)
        try:
            customers = catalog_service.customers(limit=1000)
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, tr('customer_voucher_list'))
                customers = []
            else:
                raise
        for c in customers:
            self.customer_combo.addItem(c.get('name', ''), c.get('id'))
        form.addRow(tr("customer_label"), self.customer_combo)

        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem(tr("no_supplier"), None)
        try:
            suppliers = catalog_service.suppliers(limit=1000)
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, tr('supplier_voucher_list'))
                suppliers = []
            else:
                raise
        for s in suppliers:
            self.supplier_combo.addItem(s.get('name', ''), s.get('id'))
        form.addRow(tr("supplier_label"), self.supplier_combo)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 99999999)
        self.amount_spin.setDecimals(2)
        form.addRow(tr("amount_label"), self.amount_spin)

        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItem(tr("cash"), 'cash')
        self.payment_method_combo.addItem(tr("bank_payment"), 'bank')
        form.addRow(tr("payment_method_label"), self.payment_method_combo)

        self.cashbox_combo = QComboBox()
        for c in cashbox_service.cashboxes():
            label = f"{c.get('branch_name','')} - {c.get('name','')}"
            self.cashbox_combo.addItem(label, c.get('id'))
        form.addRow(tr("cashbox") + ":", self.cashbox_combo)

        self.bank_combo = QComboBox()
        self.bank_combo.addItem(tr("select_bank_account_placeholder"), None)
        for b in cashbox_service.bank_accounts():
            label = f"{b.get('branch_name','')} - {b.get('bank_name','')} {b.get('account_name') or ''}"
            self.bank_combo.addItem(label, b.get('id'))
        form.addRow(tr("bank_account") + ":", self.bank_combo)

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        form.addRow(tr("date_label"), self.date_edit)

        self.desc_edit = QLineEdit()
        form.addRow(tr("description_label"), self.desc_edit)

        self.ref_edit = QLineEdit()
        form.addRow(tr("reference_label"), self.ref_edit)

        self.invoice_combo = QComboBox()
        self.invoice_combo.addItem(tr("no_invoice"), None)
        self._invoice_remaining_by_id = {}
        self._loading_voucher = False
        form.addRow(tr("invoice_label"), self.invoice_combo)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.save)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        apply_modern_dialog(self, tr('voucher_dialog_title'))

        def update_visibility():
            typ = self.type_combo.currentData() or "expense"
            is_cash = typ in ("receipt", "payment")
            self.customer_combo.setVisible(typ == "receipt")
            self.supplier_combo.setVisible(typ == "payment")
            self.invoice_combo.setVisible(is_cash)
            self.update_invoice_list()
        self.type_combo.currentTextChanged.connect(update_visibility)
        self.customer_combo.currentIndexChanged.connect(self.update_invoice_list)
        self.supplier_combo.currentIndexChanged.connect(self.update_invoice_list)
        self.payment_method_combo.currentIndexChanged.connect(self.update_payment_visibility)
        self.invoice_combo.currentIndexChanged.connect(self.update_amount_from_invoice)

        if self.is_edit:
            self.load_voucher_data()
        update_visibility()
        self.update_payment_visibility()

    def update_payment_visibility(self):
        is_bank = self.payment_method_combo.currentData() == 'bank'
        self.bank_combo.setVisible(is_bank)
        self.cashbox_combo.setVisible(not is_bank)

    def load_voucher_data(self):
        self._loading_voucher = True
        v = self.voucher
        type_map = {"receipt": 0, "payment": 1, "expense": 2}
        self.type_combo.setCurrentIndex(type_map.get(v['type'], 2))
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
        self._loading_voucher = False

    def _voucher_old_amount_for_invoice(self, invoice_id):
        if not self.is_edit or not self.voucher:
            return Decimal('0')
        if self.voucher.get('invoice_id') != invoice_id:
            return Decimal('0')
        try:
            return Decimal(str(self.voucher.get('amount') or 0))
        except Exception:
            return Decimal('0')

    def _add_invoice_option(self, inv):
        try:
            inv_id = inv.get('id')
            remaining = Decimal(str(inv.get('total', 0))) - Decimal(str(inv.get('paid', 0))) + self._voucher_old_amount_for_invoice(inv_id)
        except Exception:
            remaining = Decimal('0')
        if remaining <= 0:
            return
        self._invoice_remaining_by_id[inv_id] = remaining
        amount_label = currency.format_amount(currency.convert(remaining, 'USD', currency.get_display_currency()))
        self.invoice_combo.addItem(tr("remaining_invoice_amount", reference=inv.get('reference', inv_id), amount=amount_label), inv_id)

    def update_invoice_list(self):
        typ = self.type_combo.currentData() or "expense"
        entity_id = None
        if typ == "receipt":
            entity_id = self.customer_combo.currentData()
        elif typ == "payment":
            entity_id = self.supplier_combo.currentData()
        self.invoice_combo.blockSignals(True)
        self.invoice_combo.clear()
        self._invoice_remaining_by_id = {}
        self.invoice_combo.addItem(tr("no_invoice"), None)
        if not entity_id:
            self.invoice_combo.blockSignals(False)
            return
        invoices = invoice_service.unpaid_invoices(
            inv_type='sale' if typ == "receipt" else 'purchase',
            customer_id=entity_id if typ == "receipt" else None,
            supplier_id=entity_id if typ == "payment" else None,
            limit=100
        )
        seen = set()
        for inv in invoices:
            seen.add(inv.get('id'))
            self._add_invoice_option(inv)
        current_invoice_id = self.voucher.get('invoice_id') if self.is_edit and self.voucher else None
        if current_invoice_id and current_invoice_id not in seen:
            current = invoice_service.get(current_invoice_id)
            if current:
                expected_type = 'sale' if typ == "receipt" else 'purchase'
                party_ok = (
                    (typ == "receipt" and current.get('customer_id') == entity_id) or
                    (typ == "payment" and current.get('supplier_id') == entity_id)
                )
                if current.get('type') == expected_type and party_ok:
                    self._add_invoice_option(current)
        self.invoice_combo.blockSignals(False)
        self.update_amount_from_invoice()

    def update_amount_from_invoice(self):
        if getattr(self, '_loading_voucher', False):
            return
        invoice_id = self.invoice_combo.currentData()
        if not invoice_id:
            return
        remaining = self._invoice_remaining_by_id.get(invoice_id)
        if remaining is None or remaining <= 0:
            return
        amount_display = currency.convert(remaining, 'USD', currency.get_display_currency())
        self.amount_spin.setValue(float(amount_display))

    def save(self):
        typ = self.type_combo.currentData() or "expense"
        if typ == "receipt" and not self.customer_combo.currentData():
            show_toast(tr("select_customer"), "error", self)
            return
        if typ == "payment" and not self.supplier_combo.currentData():
            show_toast(tr("select_supplier"), "error", self)
            return
        if self.payment_method_combo.currentData() == 'cash' and not self.cashbox_combo.currentData():
            show_toast(tr("select_cashbox_required"), "error", self)
            return
        if self.payment_method_combo.currentData() == 'bank' and not self.bank_combo.currentData():
            show_toast(tr("select_bank_required"), "error", self)
            return
        amount_display = self.amount_spin.value()
        if amount_display <= 0:
            show_toast(tr("amount_positive_required"), "error", self)
            return
        amount_usd = currency.convert(Decimal(str(amount_display)), currency.get_display_currency(), 'USD')
        data = {
            'type': typ,
            'amount': amount_usd,
            'date': self.date_edit.date().toString("yyyy-MM-dd"),
            'description': self.desc_edit.text().strip(),
            'reference': self.ref_edit.text().strip(),
            'customer_id': self.customer_combo.currentData() if typ == "receipt" else None,
            'supplier_id': self.supplier_combo.currentData() if typ == "payment" else None,
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
                show_toast(tr("voucher_updated"), "success", self)
            else:
                voucher_service.add(data)
                show_toast(tr("voucher_added"), "success", self)
            self.accept()
        except Exception as e:
            show_toast(str(e), "error", self)



# Phase110 offline guard markers: السندات

# Phase110 stable offline UI markers:
# notify_offline_read(self, 'السندات')
