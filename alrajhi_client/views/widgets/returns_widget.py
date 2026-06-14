# -*- coding: utf-8 -*-
from decimal import Decimal
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QDateEdit, QDoubleSpinBox, QTextEdit, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox, QMenu
from views.centered_dialog import CenteredDialog
from views.custom_table_view import CustomTableView
from views.widgets.components.table_toolbar import TableToolbar
from models.table_models import GenericTableModel
from core.services.sales_return_service import sales_return_service
from core.services.purchase_return_service import purchase_return_service
from core.services.warehouse_service import warehouse_service
from core.services.cashbox_service import cashbox_service
from currency import currency
from utils import show_toast
from offline_read import is_offline_read_error, notify_offline_read
from views.widgets.modern_ui import apply_modern_widget, apply_modern_dialog
from i18n import translate, qt_layout_direction


class SalesReturnDialog(CenteredDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translate('sales_return'))
        self.resize(900, 620)
        self.invoice_map = {}
        self.line_rows = []
        layout = QVBoxLayout(self.content_widget)

        top = QHBoxLayout()
        self.invoice_combo = QComboBox()
        self.invoice_combo.setMinimumWidth(360)
        self.invoice_combo.currentIndexChanged.connect(self.load_invoice_lines)
        top.addWidget(QLabel(translate('original_invoice')))
        top.addWidget(self.invoice_combo)
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        top.addWidget(QLabel(translate('date')))
        top.addWidget(self.date_edit)
        layout.addLayout(top)

        self.lines_table = QTableWidget(0, 6)
        self.lines_table.setHorizontalHeaderLabels([translate('return_item'), translate('sold_qty'), translate('previous_returned'), translate('returnable_qty'), translate('return_qty'), translate('price')])
        self.lines_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.lines_table.cellChanged.connect(lambda *_: self.recalculate())
        layout.addWidget(self.lines_table)

        pay = QHBoxLayout()
        self.warehouse_combo = QComboBox()
        for w in warehouse_service.warehouses():
            self.warehouse_combo.addItem(w.get('name',''), w.get('id'))
        pay.addWidget(QLabel(translate('return_warehouse')))
        pay.addWidget(self.warehouse_combo)
        self.refund_spin = QDoubleSpinBox()
        self.refund_spin.setMaximum(999999999)
        self.refund_spin.setDecimals(2)
        self.refund_spin.setToolTip(translate('return_paid_now_tooltip'))
        self.refund_spin.valueChanged.connect(lambda *_: self.recalculate())
        pay.addWidget(QLabel(translate('return_paid_now')))
        pay.addWidget(self.refund_spin)
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItem(translate('settlement_credit_only'), 'credit_only')
        self.payment_method_combo.addItem(translate('settlement_cash_refund'), 'cash')
        self.payment_method_combo.addItem(translate('settlement_bank_refund'), 'bank')
        self.payment_method_combo.currentIndexChanged.connect(self._update_settlement_controls)
        pay.addWidget(QLabel(translate('return_settlement')))
        pay.addWidget(self.payment_method_combo)
        layout.addLayout(pay)

        self.settlement_hint_label = QLabel(translate('return_settlement_hint'))
        self.settlement_hint_label.setWordWrap(True)
        layout.addWidget(self.settlement_hint_label)

        cash = QHBoxLayout()
        self.cashbox_combo = QComboBox()
        for c in cashbox_service.cashboxes():
            self.cashbox_combo.addItem(c.get('name',''), c.get('id'))
        self.bank_combo = QComboBox()
        self.bank_combo.addItem(translate('none'), None)
        for b in cashbox_service.bank_accounts():
            self.bank_combo.addItem(b.get('name',''), b.get('id'))
        cash.addWidget(QLabel(translate('cashbox')))
        cash.addWidget(self.cashbox_combo)
        cash.addWidget(QLabel(translate('bank_account')))
        cash.addWidget(self.bank_combo)
        layout.addLayout(cash)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(70)
        layout.addWidget(QLabel(translate('notes')))
        layout.addWidget(self.notes_edit)
        self.summary_label = QLabel(translate('return_summary_sale', total='0', credit='0', refund='0'))
        layout.addWidget(self.summary_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(translate('save_return'))
        buttons.button(QDialogButtonBox.Cancel).setText(translate('cancel'))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._update_settlement_controls()
        self.load_invoices()
        self.install_form_shortcuts(save_handler=self.accept)

    def _update_settlement_controls(self):
        method = self.payment_method_combo.currentData()
        is_cash = method == 'cash'
        is_bank = method == 'bank'
        is_credit_only = method == 'credit_only'
        self.refund_spin.setEnabled(not is_credit_only)
        self.cashbox_combo.setEnabled(is_cash)
        self.bank_combo.setEnabled(is_bank)
        if is_credit_only and self.refund_spin.value() != 0:
            self.refund_spin.blockSignals(True)
            self.refund_spin.setValue(0)
            self.refund_spin.blockSignals(False)
        self.recalculate()

    def load_invoices(self):
        self.invoice_combo.clear()
        self.invoice_map = {}
        try:
            invoices = sales_return_service.sale_invoices(limit=500)
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, translate('sales_invoices_for_return'))
                return
            raise
        for inv in invoices:
            txt = f"{inv.get('reference','')} - {inv.get('date','')} - {inv.get('customer_name') or translate('cash_customer')} - {currency.format_amount(currency.convert(inv.get('total',0),'USD',currency.get_display_currency()))}"
            self.invoice_combo.addItem(txt, inv.get('id'))
            self.invoice_map[inv.get('id')] = inv

    def load_invoice_lines(self):
        self.lines_table.blockSignals(True)
        self.lines_table.setRowCount(0)
        self.line_rows = []
        invoice_id = self.invoice_combo.currentData()
        if not invoice_id:
            self.lines_table.blockSignals(False)
            return
        try:
            lines = sales_return_service.invoice_returnable_lines(invoice_id)
        except Exception as e:
            QMessageBox.warning(self, translate('error'), str(e))
            lines = []
        for line in lines:
            row = self.lines_table.rowCount()
            self.lines_table.insertRow(row)
            self.line_rows.append(line)
            vals = [line.get('description') or str(line.get('item_id')), line.get('sold_qty','0'), line.get('returned_qty','0'), line.get('returnable_qty','0'), '0', line.get('unit_price','0')]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                if col != 4:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.lines_table.setItem(row, col, item)
        inv = self.invoice_map.get(invoice_id) or {}
        wh_id = inv.get('warehouse_id')
        if wh_id:
            idx = self.warehouse_combo.findData(wh_id)
            if idx >= 0:
                self.warehouse_combo.setCurrentIndex(idx)
        self.lines_table.blockSignals(False)
        self.recalculate()

    def recalculate(self):
        total = Decimal('0')
        for row, line in enumerate(self.line_rows):
            try:
                qty = Decimal(str(self.lines_table.item(row, 4).text() or 0))
                total += max(Decimal('0'), qty) * Decimal(str(line.get('unit_price') or 0))
            except Exception:
                pass
        self.refund_spin.setMaximum(float(total))
        if self.payment_method_combo.currentData() == 'credit_only':
            self.refund_spin.blockSignals(True)
            self.refund_spin.setValue(0)
            self.refund_spin.blockSignals(False)
        refund = Decimal(str(self.refund_spin.value()))
        if refund > total:
            self.refund_spin.blockSignals(True)
            self.refund_spin.setValue(float(total))
            self.refund_spin.blockSignals(False)
            refund = total
        self.summary_label.setText(translate('return_summary_sale', total=currency.format_amount(total), credit=currency.format_amount(total-refund), refund=currency.format_amount(refund)))

    def accept(self):
        lines = []
        for row, line in enumerate(self.line_rows):
            try:
                qty = Decimal(str(self.lines_table.item(row, 4).text() or 0))
            except Exception:
                qty = Decimal('0')
            if qty > 0:
                lines.append({'original_invoice_line_id': line.get('id'), 'quantity': str(qty)})
        try:
            sales_return_service.create_return({
                'original_invoice_id': self.invoice_combo.currentData(),
                'date': self.date_edit.date().toString('yyyy-MM-dd'),
                'warehouse_id': self.warehouse_combo.currentData(),
                'refund_amount': '0' if self.payment_method_combo.currentData() == 'credit_only' else str(self.refund_spin.value()),
                'payment_method': 'cash' if self.payment_method_combo.currentData() == 'credit_only' else self.payment_method_combo.currentData(),
                'cashbox_id': self.cashbox_combo.currentData(),
                'bank_account_id': self.bank_combo.currentData(),
                'notes': self.notes_edit.toPlainText().strip(),
                'lines': lines,
            })
            super().accept()
        except Exception as e:
            QMessageBox.warning(self, translate('return_save_failed'), str(e))


class ReturnsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.page = 0
        self.page_size = 50
        self.total = 0
        self._init_ui()
        apply_modern_widget(self, '↩️ ' + translate('sales_returns_title'), translate('sales_returns_subtitle'))
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.toolbar = TableToolbar(translate('sales_return'), translate('search_returns'), self)
        self.toolbar.addRequested.connect(self.add_return)
        self.toolbar.deleteRequested.connect(self.cancel_selected)
        self.toolbar.edit_btn.setVisible(False)
        self.toolbar.exportRequested.connect(lambda: self.table.export_to_excel())
        self.toolbar.printRequested.connect(lambda: self.print_selected_return('preview'))
        self.toolbar.refreshRequested.connect(self.refresh)
        self.toolbar.searchChanged.connect(lambda _t: self.refresh(True))
        layout.addWidget(self.toolbar)
        self.table = CustomTableView()
        self.table.set_table_identity('ReturnsWidget.sales_returns')
        self.table.setSelectionBehavior(CustomTableView.SelectRows)
        self.toolbar.set_table(self.table)
        self._install_print_menu()
        layout.addWidget(self.table)
        pager = QHBoxLayout()
        self.prev_btn = QPushButton(translate('previous'))
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn = QPushButton(translate('next'))
        self.next_btn.clicked.connect(self.next_page)
        self.page_label = QLabel()
        pager.addWidget(self.prev_btn)
        pager.addWidget(self.page_label)
        pager.addWidget(self.next_btn)
        pager.addStretch()
        layout.addLayout(pager)

    def refresh(self, reset_page=False):
        if reset_page:
            self.page = 0
        try:
            rows, self.total = sales_return_service.list_returns(search=self.toolbar.search_edit.text().strip() or None, limit=self.page_size, offset=self.page*self.page_size)
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, translate('sales_returns'))
                return
            raise
        data = []
        for r in rows:
            data.append({
                'id': r.get('id'),
                'return_no': r.get('return_no',''),
                'date': r.get('date',''),
                'invoice': r.get('invoice_reference',''),
                'customer': r.get('customer_name') or translate('cash_customer'),
                'warehouse': r.get('warehouse_name',''),
                'total': currency.format_amount(currency.convert(r.get('total',0),'USD',currency.get_display_currency())),
                'refund': currency.format_amount(currency.convert(r.get('refund_amount',0),'USD',currency.get_display_currency())),
                'credit': currency.format_amount(currency.convert(r.get('credit_amount',0),'USD',currency.get_display_currency())),
            })
        self.model = GenericTableModel(data, [translate('return_no'), translate('date'), translate('invoice'), translate('customer'), translate('warehouse'), translate('total'), translate('refunded'), translate('credit_reduction')], key_fields=['id'], data_keys=['return_no','date','invoice','customer','warehouse','total','refund','credit'])
        self.table.setModel(self.model)
        self.table.refresh_style()
        pages = max(1, (self.total + self.page_size - 1) // self.page_size)
        self.page_label.setText(translate('page_of', page=self.page+1, pages=pages))
        self.prev_btn.setEnabled(self.page > 0)
        self.next_btn.setEnabled(self.page + 1 < pages)
        start = 0 if self.total == 0 else self.page*self.page_size + 1
        end = min(self.total, self.page*self.page_size + len(data))
        self.toolbar.set_counter(translate('showing_records', start=start, end=end, total=self.total))

    def _install_print_menu(self):
        if not hasattr(self.toolbar, 'print_btn'):
            return
        menu = QMenu(self.toolbar.print_btn)
        menu.addAction(translate('preview_in_app'), lambda: self.print_selected_return('preview'))
        menu.addAction(translate('open_html_browser'), lambda: self.print_selected_return('browser'))
        menu.addAction(translate('direct_print'), lambda: self.print_selected_return('direct'))
        menu.addAction(translate('export_pdf'), lambda: self.print_selected_return('pdf'))
        self.toolbar.print_btn.setMenu(menu)

    def print_selected_return(self, mode='preview'):
        rid = self._selected_id()
        if not rid:
            QMessageBox.information(self, translate('printing'), translate('select_return_first'))
            return
        data = sales_return_service.get(rid) or {}
        if not data:
            QMessageBox.warning(self, translate('printing'), translate('return_load_failed'))
            return
        data = dict(data)
        data.setdefault('return_type', 'sale_return')
        data.setdefault('customer_name', data.get('customer') or data.get('party_name') or translate('cash_customer'))
        from printing.printing_service import printing_service
        if mode == 'browser':
            printing_service.return_browser(data, self)
        elif mode == 'direct':
            printing_service.return_print(data, self)
        elif mode == 'pdf':
            printing_service.return_pdf(data, self)
        else:
            printing_service.return_preview(data, self)

    def add_return(self):
        dlg = SalesReturnDialog(self)
        if dlg.exec():
            show_toast(translate('sales_return_saved'), 'success', self)
            self.refresh(True)

    def _selected_id(self):
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        return self.model.get_id(rows[0].row()) if rows else None

    def cancel_selected(self):
        rid = self._selected_id()
        if not rid:
            return
        if QMessageBox.question(self, translate('confirm'), translate('confirm_cancel_sales_return')) != QMessageBox.Yes:
            return
        try:
            sales_return_service.delete_return(rid)
            show_toast(translate('return_cancelled'), 'success', self)
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, translate('cancel_failed'), str(e))

    def prev_page(self):
        if self.page > 0:
            self.page -= 1
            self.refresh()

    def next_page(self):
        if (self.page + 1) * self.page_size < self.total:
            self.page += 1
            self.refresh()


class PurchaseReturnDialog(CenteredDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translate('purchase_return'))
        self.resize(900, 620)
        self.invoice_map = {}
        self.line_rows = []
        layout = QVBoxLayout(self.content_widget)

        top = QHBoxLayout()
        self.invoice_combo = QComboBox()
        self.invoice_combo.setMinimumWidth(360)
        self.invoice_combo.currentIndexChanged.connect(self.load_invoice_lines)
        top.addWidget(QLabel(translate('original_purchase_invoice')))
        top.addWidget(self.invoice_combo)
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        top.addWidget(QLabel(translate('date')))
        top.addWidget(self.date_edit)
        layout.addLayout(top)

        self.lines_table = QTableWidget(0, 6)
        self.lines_table.setHorizontalHeaderLabels([translate('return_item'), translate('purchased_qty'), translate('previous_returned'), translate('returnable_qty'), translate('return_qty'), translate('price')])
        self.lines_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.lines_table.cellChanged.connect(lambda *_: self.recalculate())
        layout.addWidget(self.lines_table)

        pay = QHBoxLayout()
        self.warehouse_combo = QComboBox()
        for w in warehouse_service.warehouses():
            self.warehouse_combo.addItem(w.get('name',''), w.get('id'))
        pay.addWidget(QLabel(translate('output_warehouse')))
        pay.addWidget(self.warehouse_combo)
        self.refund_spin = QDoubleSpinBox()
        self.refund_spin.setMaximum(999999999)
        self.refund_spin.setDecimals(2)
        self.refund_spin.setToolTip(translate('return_paid_now_tooltip'))
        self.refund_spin.valueChanged.connect(lambda *_: self.recalculate())
        pay.addWidget(QLabel(translate('return_paid_now')))
        pay.addWidget(self.refund_spin)
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItem(translate('settlement_credit_only'), 'credit_only')
        self.payment_method_combo.addItem(translate('settlement_cash_refund_purchase'), 'cash')
        self.payment_method_combo.addItem(translate('settlement_bank_refund_purchase'), 'bank')
        self.payment_method_combo.currentIndexChanged.connect(self._update_settlement_controls)
        pay.addWidget(QLabel(translate('return_settlement')))
        pay.addWidget(self.payment_method_combo)
        layout.addLayout(pay)

        self.settlement_hint_label = QLabel(translate('return_settlement_hint_purchase'))
        self.settlement_hint_label.setWordWrap(True)
        layout.addWidget(self.settlement_hint_label)

        cash = QHBoxLayout()
        self.cashbox_combo = QComboBox()
        for c in cashbox_service.cashboxes():
            self.cashbox_combo.addItem(c.get('name',''), c.get('id'))
        self.bank_combo = QComboBox()
        self.bank_combo.addItem(translate('none'), None)
        for b in cashbox_service.bank_accounts():
            self.bank_combo.addItem(b.get('name',''), b.get('id'))
        cash.addWidget(QLabel(translate('cashbox')))
        cash.addWidget(self.cashbox_combo)
        cash.addWidget(QLabel(translate('bank_account')))
        cash.addWidget(self.bank_combo)
        layout.addLayout(cash)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(70)
        layout.addWidget(QLabel(translate('notes')))
        layout.addWidget(self.notes_edit)
        self.summary_label = QLabel(translate('return_summary_purchase', total='0', credit='0', refund='0'))
        layout.addWidget(self.summary_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(translate('save_return'))
        buttons.button(QDialogButtonBox.Cancel).setText(translate('cancel'))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._update_settlement_controls()
        self.load_invoices()
        self.install_form_shortcuts(save_handler=self.accept)

    def _update_settlement_controls(self):
        method = self.payment_method_combo.currentData()
        is_cash = method == 'cash'
        is_bank = method == 'bank'
        is_credit_only = method == 'credit_only'
        self.refund_spin.setEnabled(not is_credit_only)
        self.cashbox_combo.setEnabled(is_cash)
        self.bank_combo.setEnabled(is_bank)
        if is_credit_only and self.refund_spin.value() != 0:
            self.refund_spin.blockSignals(True)
            self.refund_spin.setValue(0)
            self.refund_spin.blockSignals(False)
        self.recalculate()

    def load_invoices(self):
        self.invoice_combo.clear()
        self.invoice_map = {}
        try:
            invoices = purchase_return_service.purchase_invoices(limit=500)
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, translate('purchase_invoices_for_return'))
                return
            raise
        for inv in invoices:
            txt = f"{inv.get('reference','')} - {inv.get('date','')} - {inv.get('supplier_name') or translate('cash_customer')} - {currency.format_amount(currency.convert(inv.get('total',0),'USD',currency.get_display_currency()))}"
            self.invoice_combo.addItem(txt, inv.get('id'))
            self.invoice_map[inv.get('id')] = inv

    def load_invoice_lines(self):
        self.lines_table.blockSignals(True)
        self.lines_table.setRowCount(0)
        self.line_rows = []
        invoice_id = self.invoice_combo.currentData()
        if not invoice_id:
            self.lines_table.blockSignals(False)
            return
        try:
            lines = purchase_return_service.invoice_returnable_lines(invoice_id)
        except Exception as e:
            QMessageBox.warning(self, translate('error'), str(e))
            lines = []
        for line in lines:
            row = self.lines_table.rowCount()
            self.lines_table.insertRow(row)
            self.line_rows.append(line)
            vals = [line.get('description') or str(line.get('item_id')), line.get('purchased_qty','0'), line.get('returned_qty','0'), line.get('returnable_qty','0'), '0', line.get('unit_price','0')]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                if col != 4:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.lines_table.setItem(row, col, item)
        inv = self.invoice_map.get(invoice_id) or {}
        wh_id = inv.get('warehouse_id')
        if wh_id:
            idx = self.warehouse_combo.findData(wh_id)
            if idx >= 0:
                self.warehouse_combo.setCurrentIndex(idx)
        self.lines_table.blockSignals(False)
        self.recalculate()

    def recalculate(self):
        total = Decimal('0')
        for row, line in enumerate(self.line_rows):
            try:
                qty = Decimal(str(self.lines_table.item(row, 4).text() or 0))
                total += max(Decimal('0'), qty) * Decimal(str(line.get('unit_price') or 0))
            except Exception:
                pass
        self.refund_spin.setMaximum(float(total))
        if self.payment_method_combo.currentData() == 'credit_only':
            self.refund_spin.blockSignals(True)
            self.refund_spin.setValue(0)
            self.refund_spin.blockSignals(False)
        refund = Decimal(str(self.refund_spin.value()))
        if refund > total:
            self.refund_spin.blockSignals(True)
            self.refund_spin.setValue(float(total))
            self.refund_spin.blockSignals(False)
            refund = total
        self.summary_label.setText(translate('return_summary_purchase', total=currency.format_amount(total), credit=currency.format_amount(total-refund), refund=currency.format_amount(refund)))

    def accept(self):
        lines = []
        for row, line in enumerate(self.line_rows):
            try:
                qty = Decimal(str(self.lines_table.item(row, 4).text() or 0))
            except Exception:
                qty = Decimal('0')
            if qty > 0:
                lines.append({'original_invoice_line_id': line.get('id'), 'quantity': str(qty)})
        try:
            purchase_return_service.create_return({
                'original_invoice_id': self.invoice_combo.currentData(),
                'date': self.date_edit.date().toString('yyyy-MM-dd'),
                'warehouse_id': self.warehouse_combo.currentData(),
                'refund_amount': '0' if self.payment_method_combo.currentData() == 'credit_only' else str(self.refund_spin.value()),
                'payment_method': 'cash' if self.payment_method_combo.currentData() == 'credit_only' else self.payment_method_combo.currentData(),
                'cashbox_id': self.cashbox_combo.currentData(),
                'bank_account_id': self.bank_combo.currentData(),
                'notes': self.notes_edit.toPlainText().strip(),
                'lines': lines,
            })
            super().accept()
        except Exception as e:
            QMessageBox.warning(self, translate('return_save_failed'), str(e))



class PurchaseReturnsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.page = 0
        self.page_size = 50
        self.total = 0
        self._init_ui()
        apply_modern_widget(self, '↩️ ' + translate('purchase_returns_title'), translate('purchase_returns_subtitle'))
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        self.toolbar = TableToolbar(translate('purchase_return'), translate('search_returns'), self)
        self.toolbar.addRequested.connect(self.add_return)
        self.toolbar.deleteRequested.connect(self.cancel_selected)
        self.toolbar.edit_btn.setVisible(False)
        self.toolbar.exportRequested.connect(lambda: self.table.export_to_excel())
        self.toolbar.printRequested.connect(lambda: self.print_selected_return('preview'))
        self.toolbar.refreshRequested.connect(self.refresh)
        self.toolbar.searchChanged.connect(lambda _t: self.refresh(True))
        layout.addWidget(self.toolbar)
        self.table = CustomTableView()
        self.table.set_table_identity('PurchaseReturnsWidget.purchase_returns')
        self.table.setSelectionBehavior(CustomTableView.SelectRows)
        self.toolbar.set_table(self.table)
        self._install_print_menu()
        layout.addWidget(self.table)
        pager = QHBoxLayout()
        self.prev_btn = QPushButton(translate('previous'))
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn = QPushButton(translate('next'))
        self.next_btn.clicked.connect(self.next_page)
        self.page_label = QLabel()
        pager.addWidget(self.prev_btn)
        pager.addWidget(self.page_label)
        pager.addWidget(self.next_btn)
        pager.addStretch()
        layout.addLayout(pager)

    def refresh(self, reset_page=False):
        if reset_page:
            self.page = 0
        try:
            rows, self.total = purchase_return_service.list_returns(search=self.toolbar.search_edit.text().strip() or None, limit=self.page_size, offset=self.page*self.page_size)
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, translate('purchase_returns'))
                return
            raise
        data = []
        for r in rows:
            data.append({
                'id': r.get('id'),
                'return_no': r.get('return_no',''),
                'date': r.get('date',''),
                'invoice': r.get('invoice_reference',''),
                'supplier': r.get('supplier_name') or translate('cash_customer'),
                'warehouse': r.get('warehouse_name',''),
                'total': currency.format_amount(currency.convert(r.get('total',0),'USD',currency.get_display_currency())),
                'refund': currency.format_amount(currency.convert(r.get('refund_amount',0),'USD',currency.get_display_currency())),
                'credit': currency.format_amount(currency.convert(r.get('credit_amount',0),'USD',currency.get_display_currency())),
            })
        self.model = GenericTableModel(data, [translate('return_no'), translate('date'), translate('invoice'), translate('supplier'), translate('warehouse'), translate('total'), translate('refunded'), translate('credit_reduction')], key_fields=['id'], data_keys=['return_no','date','invoice','supplier','warehouse','total','refund','credit'])
        self.table.setModel(self.model)
        self.table.refresh_style()
        pages = max(1, (self.total + self.page_size - 1) // self.page_size)
        self.page_label.setText(translate('page_of', page=self.page+1, pages=pages))
        self.prev_btn.setEnabled(self.page > 0)
        self.next_btn.setEnabled(self.page + 1 < pages)
        start = 0 if self.total == 0 else self.page*self.page_size + 1
        end = min(self.total, self.page*self.page_size + len(data))
        self.toolbar.set_counter(translate('showing_records', start=start, end=end, total=self.total))

    def _install_print_menu(self):
        if not hasattr(self.toolbar, 'print_btn'):
            return
        menu = QMenu(self.toolbar.print_btn)
        menu.addAction(translate('preview_in_app'), lambda: self.print_selected_return('preview'))
        menu.addAction(translate('open_html_browser'), lambda: self.print_selected_return('browser'))
        menu.addAction(translate('direct_print'), lambda: self.print_selected_return('direct'))
        menu.addAction(translate('export_pdf'), lambda: self.print_selected_return('pdf'))
        self.toolbar.print_btn.setMenu(menu)

    def print_selected_return(self, mode='preview'):
        rid = self._selected_id()
        if not rid:
            QMessageBox.information(self, translate('printing'), translate('select_return_first'))
            return
        data = purchase_return_service.get(rid) or {}
        if not data:
            QMessageBox.warning(self, translate('printing'), translate('return_load_failed'))
            return
        data = dict(data)
        data.setdefault('return_type', 'purchase_return')
        data.setdefault('supplier_name', data.get('supplier') or data.get('party_name') or translate('cash_customer'))
        from printing.printing_service import printing_service
        if mode == 'browser':
            printing_service.return_browser(data, self)
        elif mode == 'direct':
            printing_service.return_print(data, self)
        elif mode == 'pdf':
            printing_service.return_pdf(data, self)
        else:
            printing_service.return_preview(data, self)

    def add_return(self):
        dlg = PurchaseReturnDialog(self)
        if dlg.exec():
            show_toast(translate('purchase_return_saved'), 'success', self)
            self.refresh(True)

    def _selected_id(self):
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        return self.model.get_id(rows[0].row()) if rows else None

    def cancel_selected(self):
        rid = self._selected_id()
        if not rid:
            return
        if QMessageBox.question(self, translate('confirm'), translate('confirm_cancel_purchase_return')) != QMessageBox.Yes:
            return
        try:
            purchase_return_service.delete_return(rid)
            show_toast(translate('return_cancelled'), 'success', self)
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, translate('cancel_failed'), str(e))

    def prev_page(self):
        if self.page > 0:
            self.page -= 1
            self.refresh()

    def next_page(self):
        if (self.page + 1) * self.page_size < self.total:
            self.page += 1
            self.refresh()

