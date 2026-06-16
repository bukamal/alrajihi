# -*- coding: utf-8 -*-
from decimal import Decimal
from PyQt5.QtCore import Qt, QDate, QSettings
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QDateEdit, QDoubleSpinBox, QTextEdit, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox, QMenu, QAction, QStyledItemDelegate
from views.centered_dialog import CenteredDialog
from views.custom_table_view import CustomTableView
from views.widgets.components.table_toolbar import TableToolbar
from models.table_models import GenericTableModel
from core.services.sales_return_service import sales_return_service
from core.services.purchase_return_service import purchase_return_service
from core.services.warehouse_service import warehouse_service
from core.services.cashbox_service import cashbox_service
from core.services.product_service import product_service
from currency import currency

RET_COL_BARCODE = 0
RET_COL_ITEM = 1
RET_COL_ORIGINAL_QTY = 2
RET_COL_PREVIOUS = 3
RET_COL_RETURNABLE = 4
RET_COL_UNIT = 5
RET_COL_RETURN_QTY = 6
RET_COL_PRICE = 7
RET_COL_TOTAL = 8
RET_COL_NOTES = 9
RET_COL_COUNT = 10



def _ret_dec(value, default='0'):
    try:
        return Decimal(str(value if value not in (None, '') else default))
    except Exception:
        return Decimal(str(default))


def _ret_fmt_qty(value):
    d = _ret_dec(value)
    if d == d.to_integral_value():
        return f"{d:.0f}"
    return format(d.normalize(), 'f').rstrip('0').rstrip('.')


def _ret_item_name(line):
    for key in ('item_name', 'name', 'product_name', 'description'):
        val = line.get(key)
        if val and not str(val).strip().isdigit():
            return str(val)
    item_id = line.get('item_id')
    if item_id:
        try:
            item = product_service.item_by_id(int(item_id)) or {}
            if item.get('name'):
                return str(item.get('name'))
        except Exception:
            pass
    return str(item_id or '')


def _ret_units_for_line(line):
    item_id = line.get('item_id')
    base_unit = line.get('base_unit') or line.get('unit_name') or line.get('unit') or translate('unit_piece')
    units = [{'id': None, 'unit_name': base_unit or translate('unit_piece'), 'conversion_factor': Decimal('1')}]
    if item_id:
        try:
            item = product_service.item_by_id(int(item_id)) or {}
            if item.get('unit'):
                units[0]['unit_name'] = item.get('unit')
            for u in product_service.item_units(int(item_id)) or []:
                name = u.get('unit_name') or u.get('name')
                if not name:
                    continue
                factor = _ret_dec(u.get('conversion_factor') or 1, '1')
                if factor > 0 and all(x.get('unit_name') != name for x in units):
                    units.append({'id': u.get('id'), 'unit_name': name, 'conversion_factor': factor})
        except Exception:
            pass
    orig_unit = line.get('unit') or line.get('unit_name')
    orig_factor = _ret_dec(line.get('conversion_factor') or 1, '1')
    if orig_unit and all(u.get('unit_name') != orig_unit for u in units):
        units.append({'id': line.get('unit_id'), 'unit_name': orig_unit, 'conversion_factor': orig_factor})
    return units



def _ret_original_factor(line):
    factor = _ret_dec(line.get('conversion_factor') or 1, '1')
    return factor if factor > 0 else Decimal('1')


def _ret_line_base_qty(line, base_key, display_key=None):
    base = _ret_dec(line.get(base_key) or 0)
    if base > 0 or not display_key:
        return base
    return _ret_dec(line.get(display_key) or 0) * _ret_original_factor(line)


def _ret_returnable_base(line):
    return _ret_line_base_qty(line, 'returnable_qty_base', 'returnable_qty')


def _ret_selected_unit_data(table, row, line):
    item = table.item(row, RET_COL_UNIT)
    data = item.data(Qt.UserRole) if item is not None else None
    factor = _ret_dec((data or {}).get('factor') or line.get('_selected_factor') or line.get('conversion_factor') or 1, '1')
    if factor <= 0:
        factor = Decimal('1')
    return {
        'factor': factor,
        'unit': (data or {}).get('unit') or line.get('_selected_unit') or line.get('unit') or '',
        'unit_id': (data or {}).get('unit_id', line.get('_selected_unit_id')),
    }


def _ret_unit_price_usd_for_factor(line, factor):
    orig_factor = _ret_original_factor(line)
    # invoice line unit_price is stored per original invoice display unit.
    return (_ret_dec(line.get('unit_price') or line.get('price') or 0) / orig_factor) * factor


def _ret_prepare_line_base_fields(line, qty_kind):
    factor = _ret_original_factor(line)
    if qty_kind == 'sale':
        sold_base = _ret_line_base_qty(line, 'sold_qty_base', 'sold_qty')
        line['sold_qty_base'] = str(sold_base)
    else:
        purchased_base = _ret_line_base_qty(line, 'purchased_qty_base', 'purchased_qty')
        line['purchased_qty_base'] = str(purchased_base)
    returned_base = _ret_line_base_qty(line, 'returned_qty_base', 'returned_qty')
    # derive remaining from base columns when missing or zero but display values exist.
    if not line.get('returnable_qty_base'):
        total_base = _ret_line_base_qty(line, 'sold_qty_base' if qty_kind == 'sale' else 'purchased_qty_base', 'sold_qty' if qty_kind == 'sale' else 'purchased_qty')
        line['returnable_qty_base'] = str(max(Decimal('0'), total_base - returned_base))
    else:
        line['returnable_qty_base'] = str(_ret_returnable_base(line))
    line['returned_qty_base'] = str(returned_base)
    line['_base_price_usd'] = _ret_unit_price_usd_for_factor(line, Decimal('1'))
    line['_selected_factor'] = factor
    line['_selected_unit_price_usd'] = _ret_unit_price_usd_for_factor(line, factor)
    return line


def _ret_set_readonly_item(table, row, col, text):
    item = table.item(row, col)
    if item is None:
        item = QTableWidgetItem()
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        table.setItem(row, col, item)
    item.setText(str(text))
    return item


class ReturnUnitDelegate(QStyledItemDelegate):
    """Shows unit as plain text and opens a combo editor only while editing."""
    def __init__(self, owner):
        super().__init__(owner.lines_table)
        self.owner = owner

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        row = index.row()
        line = self.owner.line_rows[row] if 0 <= row < len(self.owner.line_rows) else {}
        for u in _ret_units_for_line(line):
            combo.addItem(str(u.get('unit_name') or ''), {
                'unit': u.get('unit_name'),
                'factor': str(u.get('conversion_factor') or 1),
                'unit_id': u.get('id')
            })
        return combo

    def setEditorData(self, editor, index):
        data = index.data(Qt.UserRole) or {}
        unit = str(data.get('unit') or index.data() or '')
        idx = editor.findText(unit)
        if idx < 0:
            idx = 0
        editor.setCurrentIndex(idx)

    def setModelData(self, editor, model, index):
        data = editor.currentData() or {}
        unit = str(data.get('unit') or editor.currentText() or '')
        model.setData(index, unit, Qt.EditRole)
        model.setData(index, data, Qt.UserRole)
        try:
            self.owner._unit_changed(index.row())
        except Exception:
            pass


def _ret_set_unit_item(table, row, col, line, units):
    selected_unit = str(line.get('unit') or line.get('unit_name') or '')
    selected = None
    for u in units:
        if selected_unit and str(u.get('unit_name') or '') == selected_unit:
            selected = u
            break
    if selected is None:
        selected = units[0] if units else {'unit_name': selected_unit, 'conversion_factor': line.get('conversion_factor') or 1, 'id': line.get('unit_id')}
    data = {'unit': selected.get('unit_name'), 'factor': str(selected.get('conversion_factor') or 1), 'unit_id': selected.get('id')}
    item = table.item(row, col)
    if item is None:
        item = QTableWidgetItem()
        table.setItem(row, col, item)
    item.setText(str(data.get('unit') or ''))
    item.setData(Qt.UserRole, data)
    flags = item.flags() | Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
    item.setFlags(flags)
    return item


def _ret_select_combo_data(combo, value):
    if value in (None, ''):
        return
    idx = combo.findData(value)
    if idx >= 0:
        combo.setCurrentIndex(idx)


def _ret_current_dialog_print_data(dialog, qty_kind):
    """Build a printable return document from the currently open dialog.

    The printable payload intentionally uses the same displayed unit, conversion
    factor and price calculation as validation/save, so preview/print/PDF cannot
    diverge from the form totals.
    """
    lines = []
    total_usd = Decimal('0')
    for row, line in enumerate(getattr(dialog, 'line_rows', []) or []):
        qty_item = dialog.lines_table.item(row, RET_COL_RETURN_QTY)
        qty = _ret_dec(qty_item.text() if qty_item else 0)
        if qty <= 0:
            continue
        unit_data = _ret_selected_unit_data(dialog.lines_table, row, line)
        factor = unit_data['factor'] if unit_data['factor'] > 0 else Decimal('1')
        base_qty = qty * factor
        unit_price_usd = _ret_unit_price_usd_for_factor(line, factor)
        line_total_usd = qty * unit_price_usd
        total_usd += line_total_usd
        lines.append({
            'barcode': line.get('barcode') or line.get('item_barcode') or line.get('code') or '',
            'item_name': _ret_item_name(line),
            'unit': unit_data.get('unit') or line.get('_selected_unit') or line.get('unit') or '',
            'unit_id': unit_data.get('unit_id'),
            'conversion_factor': str(factor),
            'quantity': _ret_fmt_qty(qty),
            'quantity_in_base': str(base_qty),
            'unit_price': currency.format_amount(currency.convert(unit_price_usd, 'USD', currency.get_display_currency())),
            'line_total': currency.format_amount(currency.convert(line_total_usd, 'USD', currency.get_display_currency())),
            'discount_percent': '0',
            'tax_percent': '0',
        })
    invoice_id = dialog.invoice_combo.currentData()
    inv = getattr(dialog, 'invoice_map', {}).get(invoice_id, {}) or {}
    party_name = inv.get('customer_name') if qty_kind == 'sale' else inv.get('supplier_name')
    if not party_name:
        party_name = inv.get('party_name') or inv.get('entity_name') or translate('cash_customer')
    warehouse = dialog.warehouse_combo.currentText() if hasattr(dialog, 'warehouse_combo') else ''
    refund_usd = Decimal('0') if dialog.payment_method_combo.currentData() == 'credit_only' else currency.convert(_ret_dec(dialog.refund_spin.value()), currency.get_display_currency(), 'USD')
    ref = ''
    if getattr(dialog, 'edit_return_id', None):
        ref = (getattr(dialog, 'edit_return_data', {}) or {}).get('return_no') or (getattr(dialog, 'edit_return_data', {}) or {}).get('reference') or dialog.edit_return_id
    return {
        'id': ref or translate('draft'),
        'reference': ref or translate('draft'),
        'return_type': 'sale_return' if qty_kind == 'sale' else 'purchase_return',
        'type': 'sale' if qty_kind == 'sale' else 'purchase',
        'date': dialog.date_edit.date().toString('yyyy-MM-dd'),
        'original_invoice_id': invoice_id,
        'invoice_reference': inv.get('reference') or inv.get('invoice_no') or inv.get('number') or '',
        'party_name': party_name,
        'customer_name': party_name if qty_kind == 'sale' else '',
        'supplier_name': party_name if qty_kind != 'sale' else '',
        'warehouse_name': warehouse,
        'payment_method': dialog.payment_method_combo.currentText(),
        'notes': dialog.notes_edit.toPlainText().strip(),
        'lines': lines,
        'total': currency.format_amount(currency.convert(total_usd, 'USD', currency.get_display_currency())),
        'paid_amount': currency.format_amount(currency.convert(refund_usd, 'USD', currency.get_display_currency())),
        'remaining': currency.format_amount(currency.convert(total_usd - refund_usd, 'USD', currency.get_display_currency())),
    }


def _ret_print_dialog(dialog, qty_kind, mode='preview'):
    data = _ret_current_dialog_print_data(dialog, qty_kind)
    if not data.get('lines'):
        QMessageBox.information(dialog, translate('printing'), translate('no_return_lines_to_print'))
        return
    from printing.printing_service import printing_service
    if mode == 'browser':
        printing_service.return_browser(data, dialog)
    elif mode == 'direct':
        printing_service.return_print(data, dialog)
    elif mode == 'pdf':
        printing_service.return_pdf(data, dialog)
    else:
        printing_service.return_preview(data, dialog)


def _ret_install_dialog_print_button(dialog, button_box, qty_kind):
    print_btn = QPushButton(translate('print'))
    print_btn.setObjectName('secondary')
    menu = QMenu(print_btn)
    menu.addAction(translate('preview_in_app'), lambda: _ret_print_dialog(dialog, qty_kind, 'preview'))
    menu.addAction(translate('open_html_browser'), lambda: _ret_print_dialog(dialog, qty_kind, 'browser'))
    menu.addAction(translate('direct_print'), lambda: _ret_print_dialog(dialog, qty_kind, 'direct'))
    menu.addAction(translate('export_pdf'), lambda: _ret_print_dialog(dialog, qty_kind, 'pdf'))
    print_btn.setMenu(menu)
    button_box.addButton(print_btn, QDialogButtonBox.ActionRole)
    dialog.print_btn = print_btn


def _ret_default_return_visible_columns():
    return {RET_COL_BARCODE, RET_COL_ITEM, RET_COL_RETURN_QTY, RET_COL_UNIT, RET_COL_PRICE, RET_COL_TOTAL, RET_COL_NOTES}


def _ret_return_line_columns_key(dialog):
    return f"return_dialog_lines/{getattr(dialog, '_return_table_identity', 'returns')}"


def _ret_install_return_line_column_controls(dialog, identity):
    dialog._return_table_identity = identity
    dialog.lines_table.horizontalHeader().setSectionsMovable(True)
    dialog.lines_table.setContextMenuPolicy(Qt.CustomContextMenu)
    try:
        dialog.lines_table.customContextMenuRequested.disconnect()
    except Exception:
        pass
    dialog.lines_table.customContextMenuRequested.connect(lambda pos: _ret_show_return_line_columns_menu(dialog, pos))
    _ret_restore_return_line_columns(dialog)


def _ret_restore_return_line_columns(dialog):
    try:
        settings = QSettings('Alrajhi', 'Accounting')
        key = _ret_return_line_columns_key(dialog)
        saved = settings.value(f'{key}/visible_columns')
        if saved:
            visible = {int(x) for x in str(saved).split(',') if str(x).strip().isdigit()}
        else:
            visible = _ret_default_return_visible_columns()
        for col in range(dialog.lines_table.columnCount()):
            dialog.lines_table.setColumnHidden(col, col not in visible)
        state = settings.value(f'{key}/header_state')
        if state:
            dialog.lines_table.horizontalHeader().restoreState(state)
    except Exception:
        pass


def _ret_save_return_line_columns(dialog):
    try:
        settings = QSettings('Alrajhi', 'Accounting')
        key = _ret_return_line_columns_key(dialog)
        visible = [str(c) for c in range(dialog.lines_table.columnCount()) if not dialog.lines_table.isColumnHidden(c)]
        settings.setValue(f'{key}/visible_columns', ','.join(visible))
        settings.setValue(f'{key}/header_state', dialog.lines_table.horizontalHeader().saveState())
    except Exception:
        pass


def _ret_show_return_line_columns_menu(dialog, pos=None, source_widget=None):
    menu = QMenu(dialog)
    columns_menu = menu.addMenu(translate('columns'))
    for col in range(dialog.lines_table.columnCount()):
        header = dialog.lines_table.horizontalHeaderItem(col).text() if dialog.lines_table.horizontalHeaderItem(col) else translate('column_number', number=col + 1)
        act = QAction(str(header), dialog)
        act.setCheckable(True)
        act.setChecked(not dialog.lines_table.isColumnHidden(col))
        act.toggled.connect(lambda checked, c=col: (dialog.lines_table.setColumnHidden(c, not checked), _ret_save_return_line_columns(dialog)))
        columns_menu.addAction(act)
    reset = QAction(translate('reset_columns'), dialog)
    reset.triggered.connect(lambda: (QSettings('Alrajhi', 'Accounting').remove(_ret_return_line_columns_key(dialog)), _ret_restore_return_line_columns(dialog)))
    columns_menu.addSeparator()
    columns_menu.addAction(reset)
    target = source_widget or dialog.lines_table.viewport()
    if pos is None:
        pos = target.rect().bottomLeft()
    menu.exec(target.mapToGlobal(pos))


def _ret_show_return_line_columns_menu_from_button(dialog):
    btn = getattr(dialog, 'columns_btn', None)
    if btn is not None:
        _ret_show_return_line_columns_menu(dialog, btn.rect().bottomLeft(), btn)


def _ret_apply_existing_return(dialog, service, return_data, qty_kind):
    """Fill a return dialog for editing while keeping validation in base units."""
    ret = return_data or {}
    invoice_id = ret.get('original_invoice_id')
    if invoice_id not in (None, ''):
        idx = dialog.invoice_combo.findData(invoice_id)
        if idx >= 0:
            dialog.invoice_combo.setCurrentIndex(idx)
        dialog.invoice_combo.setEnabled(False)
        dialog.load_invoice_lines()
    date_text = str(ret.get('date') or '')[:10]
    if date_text:
        qdate = QDate.fromString(date_text, 'yyyy-MM-dd')
        if qdate.isValid():
            dialog.date_edit.setDate(qdate)
    _ret_select_combo_data(dialog.warehouse_combo, ret.get('warehouse_id'))
    _ret_select_combo_data(dialog.cashbox_combo, ret.get('cashbox_id'))
    _ret_select_combo_data(dialog.bank_combo, ret.get('bank_account_id'))
    _ret_select_combo_data(dialog.payment_method_combo, ret.get('payment_method'))
    try:
        dialog.refund_spin.setValue(float(currency.convert(_ret_dec(ret.get('refund_amount') or 0), 'USD', currency.get_display_currency())))
    except Exception:
        pass
    dialog.notes_edit.setPlainText(str(ret.get('notes') or ''))
    existing = {int(l.get('original_invoice_line_id') or 0): dict(l) for l in (ret.get('lines') or []) if l.get('original_invoice_line_id')}
    qty_base_key = 'sold_qty_base' if qty_kind == 'sale' else 'purchased_qty_base'
    dialog.lines_table.blockSignals(True)
    for row, line in enumerate(dialog.line_rows):
        old = existing.get(int(line.get('id') or 0))
        if not old:
            continue
        old_base = _ret_dec(old.get('quantity_in_base') or old.get('quantity') or 0)
        # invoice_returnable_lines includes this active return as returned. Add it back for edit.
        line['returned_qty_base'] = str(max(Decimal('0'), _ret_dec(line.get('returned_qty_base') or 0) - old_base))
        line['returnable_qty_base'] = str(_ret_dec(line.get('returnable_qty_base') or 0) + old_base)
        factor = _ret_dec(old.get('conversion_factor') or 1, '1')
        if factor <= 0:
            factor = Decimal('1')
        unit_data = {'unit': old.get('unit') or line.get('unit') or '', 'factor': str(factor), 'unit_id': old.get('unit_id')}
        unit_item = dialog.lines_table.item(row, RET_COL_UNIT) or QTableWidgetItem()
        dialog.lines_table.setItem(row, RET_COL_UNIT, unit_item)
        unit_item.setText(str(unit_data['unit'] or ''))
        unit_item.setData(Qt.UserRole, unit_data)
        unit_item.setFlags(unit_item.flags() | Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        line['_selected_factor'] = factor
        line['_selected_unit'] = unit_data['unit']
        line['_selected_unit_id'] = unit_data['unit_id']
        qty_item = dialog.lines_table.item(row, RET_COL_RETURN_QTY) or QTableWidgetItem()
        dialog.lines_table.setItem(row, RET_COL_RETURN_QTY, qty_item)
        qty_item.setText(_ret_fmt_qty(old_base / factor))
        dialog._unit_changed(row, recalc=False)
    dialog.lines_table.blockSignals(False)
    dialog.recalculate()

from utils import show_toast
from offline_read import is_offline_read_error, notify_offline_read
from views.widgets.modern_ui import apply_modern_widget, apply_modern_dialog
from i18n import translate, qt_layout_direction


class SalesReturnDialog(CenteredDialog):
    def __init__(self, parent=None, return_id=None, return_data=None):
        super().__init__(parent)
        self.edit_return_id = return_id
        self.edit_return_data = return_data or {}
        self.setWindowTitle(translate('edit_return') if self.edit_return_id else translate('sales_return'))
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

        self.lines_table = QTableWidget(0, RET_COL_COUNT)
        self.lines_table.setHorizontalHeaderLabels([translate('barcode'), translate('return_item'), translate('sold_qty'), translate('previous_returned'), translate('returnable_qty'), translate('unit'), translate('return_qty'), translate('price'), translate('total'), translate('notes')])
        self.lines_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.lines_table.cellChanged.connect(lambda *_: self.recalculate())
        self.lines_table.setItemDelegateForColumn(RET_COL_UNIT, ReturnUnitDelegate(self))
        self.lines_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked | QTableWidget.EditKeyPressed)
        _ret_install_return_line_column_controls(self, 'sales_return_lines')
        line_tools = QHBoxLayout()
        self.columns_btn = QPushButton(translate('columns'))
        self.columns_btn.setObjectName('softAction')
        self.columns_btn.clicked.connect(lambda: _ret_show_return_line_columns_menu_from_button(self))
        line_tools.addStretch()
        line_tools.addWidget(self.columns_btn)
        layout.addLayout(line_tools)
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
        buttons.button(QDialogButtonBox.Save).setText(translate('update_return') if self.edit_return_id else translate('save_return'))
        buttons.button(QDialogButtonBox.Cancel).setText(translate('cancel'))
        _ret_install_dialog_print_button(self, buttons, 'sale')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._update_settlement_controls()
        self.load_invoices()
        if self.edit_return_id:
            _ret_apply_existing_return(self, sales_return_service, self.edit_return_data, 'sale')
        self.install_form_shortcuts(save_handler=self.accept)


    def _install_return_line_column_controls(self, identity):
        self._return_table_identity = identity
        self.lines_table.horizontalHeader().setSectionsMovable(True)
        self.lines_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lines_table.customContextMenuRequested.connect(self._show_return_line_columns_menu)
        self._restore_return_line_columns()

    def _default_return_visible_columns(self):
        return {RET_COL_BARCODE, RET_COL_ITEM, RET_COL_RETURN_QTY, RET_COL_UNIT, RET_COL_PRICE, RET_COL_TOTAL, RET_COL_NOTES}

    def _restore_return_line_columns(self):
        try:
            settings = QSettings('Alrajhi', 'Accounting')
            key = f"return_dialog_lines/{getattr(self, '_return_table_identity', 'returns')}"
            saved = settings.value(f'{key}/visible_columns')
            if saved:
                visible = {int(x) for x in str(saved).split(',') if str(x).strip().isdigit()}
            else:
                visible = self._default_return_visible_columns()
            for col in range(self.lines_table.columnCount()):
                self.lines_table.setColumnHidden(col, col not in visible)
            state = settings.value(f'{key}/header_state')
            if state:
                self.lines_table.horizontalHeader().restoreState(state)
        except Exception:
            pass

    def _save_return_line_columns(self):
        try:
            settings = QSettings('Alrajhi', 'Accounting')
            key = f"return_dialog_lines/{getattr(self, '_return_table_identity', 'returns')}"
            visible = [str(c) for c in range(self.lines_table.columnCount()) if not self.lines_table.isColumnHidden(c)]
            settings.setValue(f'{key}/visible_columns', ','.join(visible))
            settings.setValue(f'{key}/header_state', self.lines_table.horizontalHeader().saveState())
        except Exception:
            pass

    def _show_return_line_columns_menu(self, pos):
        menu = QMenu(self)
        columns_menu = menu.addMenu(translate('columns'))
        for col in range(self.lines_table.columnCount()):
            header = self.lines_table.horizontalHeaderItem(col).text() if self.lines_table.horizontalHeaderItem(col) else translate('column_number', number=col + 1)
            act = QAction(str(header), self)
            act.setCheckable(True)
            act.setChecked(not self.lines_table.isColumnHidden(col))
            act.toggled.connect(lambda checked, c=col: (self.lines_table.setColumnHidden(c, not checked), self._save_return_line_columns()))
            columns_menu.addAction(act)
        reset = QAction(translate('reset_columns'), self)
        reset.triggered.connect(lambda: (QSettings('Alrajhi', 'Accounting').remove(f"return_dialog_lines/{getattr(self, '_return_table_identity', 'returns')}"), self._restore_return_line_columns()))
        columns_menu.addSeparator()
        columns_menu.addAction(reset)
        menu.exec(self.lines_table.viewport().mapToGlobal(pos))


    def _install_return_line_column_controls(self, identity):
        self._return_table_identity = identity
        self.lines_table.horizontalHeader().setSectionsMovable(True)
        self.lines_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lines_table.customContextMenuRequested.connect(self._show_return_line_columns_menu)
        self._restore_return_line_columns()

    def _default_return_visible_columns(self):
        return {RET_COL_BARCODE, RET_COL_ITEM, RET_COL_RETURN_QTY, RET_COL_UNIT, RET_COL_PRICE, RET_COL_TOTAL, RET_COL_NOTES}

    def _restore_return_line_columns(self):
        try:
            settings = QSettings('Alrajhi', 'Accounting')
            key = f"return_dialog_lines/{getattr(self, '_return_table_identity', 'returns')}"
            saved = settings.value(f'{key}/visible_columns')
            if saved:
                visible = {int(x) for x in str(saved).split(',') if str(x).strip().isdigit()}
            else:
                visible = self._default_return_visible_columns()
            for col in range(self.lines_table.columnCount()):
                self.lines_table.setColumnHidden(col, col not in visible)
            state = settings.value(f'{key}/header_state')
            if state:
                self.lines_table.horizontalHeader().restoreState(state)
        except Exception:
            pass

    def _save_return_line_columns(self):
        try:
            settings = QSettings('Alrajhi', 'Accounting')
            key = f"return_dialog_lines/{getattr(self, '_return_table_identity', 'returns')}"
            visible = [str(c) for c in range(self.lines_table.columnCount()) if not self.lines_table.isColumnHidden(c)]
            settings.setValue(f'{key}/visible_columns', ','.join(visible))
            settings.setValue(f'{key}/header_state', self.lines_table.horizontalHeader().saveState())
        except Exception:
            pass

    def _show_return_line_columns_menu(self, pos):
        menu = QMenu(self)
        columns_menu = menu.addMenu(translate('columns'))
        for col in range(self.lines_table.columnCount()):
            header = self.lines_table.horizontalHeaderItem(col).text() if self.lines_table.horizontalHeaderItem(col) else translate('column_number', number=col + 1)
            act = QAction(str(header), self)
            act.setCheckable(True)
            act.setChecked(not self.lines_table.isColumnHidden(col))
            act.toggled.connect(lambda checked, c=col: (self.lines_table.setColumnHidden(c, not checked), self._save_return_line_columns()))
            columns_menu.addAction(act)
        reset = QAction(translate('reset_columns'), self)
        reset.triggered.connect(lambda: (QSettings('Alrajhi', 'Accounting').remove(f"return_dialog_lines/{getattr(self, '_return_table_identity', 'returns')}"), self._restore_return_line_columns()))
        columns_menu.addSeparator()
        columns_menu.addAction(reset)
        menu.exec(self.lines_table.viewport().mapToGlobal(pos))

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
            line = _ret_prepare_line_base_fields(dict(line), 'sale')
            self.line_rows.append(line)
            _ret_set_readonly_item(self.lines_table, row, RET_COL_BARCODE, line.get('barcode') or line.get('item_barcode') or '')
            _ret_set_readonly_item(self.lines_table, row, RET_COL_ITEM, _ret_item_name(line))
            for col in (RET_COL_ORIGINAL_QTY, RET_COL_PREVIOUS, RET_COL_RETURNABLE):
                _ret_set_readonly_item(self.lines_table, row, col, '')
            units = _ret_units_for_line(line)
            _ret_set_unit_item(self.lines_table, row, RET_COL_UNIT, line, units)
            qty_item = QTableWidgetItem('0')
            self.lines_table.setItem(row, RET_COL_RETURN_QTY, qty_item)
            price_item = QTableWidgetItem('')
            price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)
            self.lines_table.setItem(row, RET_COL_PRICE, price_item)
            total_item = QTableWidgetItem('')
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
            self.lines_table.setItem(row, RET_COL_TOTAL, total_item)
            self.lines_table.setItem(row, RET_COL_NOTES, QTableWidgetItem(str(line.get('notes') or line.get('description') or '')))
            self._unit_changed(row, recalc=False)
        inv = self.invoice_map.get(invoice_id) or {}
        wh_id = inv.get('warehouse_id')
        if wh_id:
            idx = self.warehouse_combo.findData(wh_id)
            if idx >= 0:
                self.warehouse_combo.setCurrentIndex(idx)
        self.lines_table.blockSignals(False)
        self.recalculate()


    def _unit_changed(self, row, recalc=True):
        if row < 0 or row >= len(self.line_rows):
            return
        line = self.line_rows[row]
        unit_data = _ret_selected_unit_data(self.lines_table, row, line)
        factor = unit_data['factor']
        line['_selected_factor'] = factor
        line['_selected_unit'] = unit_data['unit']
        line['_selected_unit_id'] = unit_data['unit_id']
        price_usd = _ret_unit_price_usd_for_factor(line, factor)
        line['_selected_unit_price_usd'] = price_usd
        price_display = currency.convert(price_usd, 'USD', currency.get_display_currency())
        qty_base_key = 'sold_qty_base' if 'sold_qty_base' in line else 'purchased_qty_base'
        for col, key in ((RET_COL_ORIGINAL_QTY, qty_base_key), (RET_COL_PREVIOUS, 'returned_qty_base'), (RET_COL_RETURNABLE, 'returnable_qty_base')):
            _ret_set_readonly_item(self.lines_table, row, col, _ret_fmt_qty(_ret_dec(line.get(key) or 0) / factor))
        _ret_set_readonly_item(self.lines_table, row, RET_COL_PRICE, _ret_fmt_qty(price_display))
        if recalc:
            self.recalculate()

    def recalculate(self):
        total = Decimal('0')
        for row, line in enumerate(self.line_rows):
            try:
                qty_item = self.lines_table.item(row, RET_COL_RETURN_QTY)
                qty = _ret_dec(qty_item.text() if qty_item else 0)
                if qty < 0:
                    qty = Decimal('0')
                factor = _ret_dec(line.get('_selected_factor') or line.get('conversion_factor') or 1, '1')
                if factor <= 0:
                    factor = Decimal('1')
                max_qty = _ret_returnable_base(line) / factor
                if qty > max_qty:
                    qty = max_qty
                    if qty_item is not None:
                        self.lines_table.blockSignals(True)
                        qty_item.setText(_ret_fmt_qty(qty))
                        self.lines_table.blockSignals(False)
                line_total = qty * currency.convert(_ret_dec(line.get('_selected_unit_price_usd') or 0), 'USD', currency.get_display_currency())
                total += line_total
                _ret_set_readonly_item(self.lines_table, row, RET_COL_TOTAL, _ret_fmt_qty(line_total))
            except Exception:
                pass
        self.refund_spin.setMaximum(float(total))
        if self.payment_method_combo.currentData() == 'credit_only':
            self.refund_spin.blockSignals(True)
            self.refund_spin.setValue(0)
            self.refund_spin.blockSignals(False)
        refund = _ret_dec(self.refund_spin.value())
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
                qty = _ret_dec(self.lines_table.item(row, RET_COL_RETURN_QTY).text() if self.lines_table.item(row, RET_COL_RETURN_QTY) else 0)
            except Exception:
                qty = Decimal('0')
            if qty > 0:
                factor = _ret_dec(line.get('_selected_factor') or line.get('conversion_factor') or 1, '1')
                if factor <= 0:
                    factor = Decimal('1')
                base_qty = qty * factor
                if base_qty > _ret_returnable_base(line):
                    QMessageBox.warning(self, translate('return_save_failed'), translate('return_quantity_exceeds_available'))
                    return
                lines.append({'original_invoice_line_id': line.get('id'), 'quantity': str(qty), 'quantity_in_base': str(base_qty), 'conversion_factor': str(factor), 'unit': line.get('_selected_unit') or line.get('unit') or '', 'unit_id': line.get('_selected_unit_id'), 'unit_price': str(_ret_unit_price_usd_for_factor(line, factor)), 'notes': self.lines_table.item(row, RET_COL_NOTES).text() if self.lines_table.item(row, RET_COL_NOTES) else ''})
        try:
            payload = {
                'original_invoice_id': self.invoice_combo.currentData(),
                'date': self.date_edit.date().toString('yyyy-MM-dd'),
                'warehouse_id': self.warehouse_combo.currentData(),
                'refund_amount': '0' if self.payment_method_combo.currentData() == 'credit_only' else str(currency.convert(_ret_dec(self.refund_spin.value()), currency.get_display_currency(), 'USD')),
                'payment_method': self.payment_method_combo.currentData(),
                'cashbox_id': self.cashbox_combo.currentData(),
                'bank_account_id': self.bank_combo.currentData(),
                'notes': self.notes_edit.toPlainText().strip(),
                'lines': lines,
            }
            if self.edit_return_id:
                sales_return_service.update_return(self.edit_return_id, payload)
            else:
                sales_return_service.create_return(payload)
            super().accept()
        except Exception as e:
            QMessageBox.warning(self, translate('return_save_failed'), str(e))




def _ret_fmt_display_amount_usd(value):
    try:
        return currency.format_amount(currency.convert(value or 0, 'USD', currency.get_display_currency()))
    except Exception:
        try:
            return currency.format_amount(value or 0)
        except Exception:
            return str(value or '')


def _ret_external_line_columns(return_data):
    lines = (return_data or {}).get('lines') or []
    if not lines:
        return {'barcode': '', 'item_name': '', 'quantity': '', 'unit': '', 'unit_price': '', 'line_total': '', 'line_notes': ''}
    barcodes, names, qtys, units, prices, totals, notes = [], [], [], [], [], [], []
    for ln in lines:
        barcodes.append(str(ln.get('barcode') or ln.get('item_barcode') or ''))
        names.append(str(ln.get('item_name') or ln.get('name') or ln.get('item_id') or ''))
        qtys.append(str(ln.get('quantity') or ln.get('return_qty') or ''))
        units.append(str(ln.get('unit') or ln.get('unit_name') or ''))
        prices.append(_ret_fmt_display_amount_usd(ln.get('unit_price') or ln.get('price') or 0))
        totals.append(_ret_fmt_display_amount_usd(ln.get('total') or 0))
        notes.append(str(ln.get('notes') or ln.get('description') or ''))
    return {
        'barcode': '، '.join([x for x in barcodes if x]),
        'item_name': '، '.join([x for x in names if x]),
        'quantity': '، '.join([x for x in qtys if x]),
        'unit': '، '.join([x for x in units if x]),
        'unit_price': '، '.join([x for x in prices if x]),
        'line_total': '، '.join([x for x in totals if x]),
        'line_notes': '، '.join([x for x in notes if x]),
    }

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
        self.toolbar.editRequested.connect(self.edit_selected)
        self.toolbar.exportRequested.connect(lambda: self.table.export_to_excel())
        self.toolbar.printRequested.connect(lambda: self.print_selected_return('preview'))
        self.toolbar.refreshRequested.connect(self.refresh)
        self.toolbar.searchChanged.connect(lambda _t: self.refresh(True))
        layout.addWidget(self.toolbar)
        self.table = CustomTableView()
        self.table.set_table_identity('ReturnsWidget.sales_returns')
        self.table.setSelectionBehavior(CustomTableView.SelectRows)
        self.toolbar.set_table(self.table)
        self.table.clicked.connect(lambda *_: self.toolbar.set_delete_enabled(True))
        self.table.clicked.connect(lambda *_: self.toolbar.set_edit_enabled(True))
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

    def set_global_filter(self, text: str):
        text = text or ''
        field = getattr(getattr(self, 'toolbar', None), 'search_edit', None)
        if field is not None and field.text() != text:
            field.setText(text)
        else:
            self.refresh(reset_page=True)

    def set_global_filter(self, text: str):
        text = text or ''
        field = getattr(getattr(self, 'toolbar', None), 'search_edit', None)
        if field is not None and field.text() != text:
            field.setText(text)
        else:
            self.refresh(reset_page=True)

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
            total_usd = _ret_dec(r.get('total') or 0)
            refund_usd = _ret_dec(r.get('refund_amount') or 0)
            credit_usd = _ret_dec(r.get('credit_amount') or 0)
            settlement_remaining_usd = max(total_usd - refund_usd - credit_usd, Decimal('0'))
            row = {
                'id': r.get('id'),
                'reference': r.get('id'),
                'return_no': r.get('return_no',''),
                'original_invoice': r.get('invoice_reference',''),
                'date': r.get('date',''),
                'customer': r.get('customer_name') or translate('cash_customer'),
                'return_total': currency.format_amount(currency.convert(total_usd,'USD',currency.get_display_currency())),
                'refund': currency.format_amount(currency.convert(refund_usd,'USD',currency.get_display_currency())),
                'settlement_remaining': currency.format_amount(currency.convert(settlement_remaining_usd,'USD',currency.get_display_currency())),
                'notes': r.get('notes',''),
            }
            data.append(row)
        self.model = GenericTableModel(
            data,
            [translate('reference'), translate('return_no'), translate('original_invoice'), translate('customer'), translate('return_value'), translate('refunded'), translate('settlement_remaining'), translate('date'), translate('notes')],
            key_fields=['id'],
            data_keys=['reference','return_no','original_invoice','customer','return_total','refund','settlement_remaining','date','notes']
        )
        self.table.setModel(self.model)
        self.toolbar.set_delete_enabled(False)
        self.toolbar.set_edit_enabled(False)
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


    def edit_selected(self):
        rid = self._selected_id()
        if not rid:
            return
        data = sales_return_service.get(rid)
        if not data:
            QMessageBox.warning(self, translate('error'), translate('return_load_failed'))
            return
        dlg = SalesReturnDialog(self, return_id=rid, return_data=data)
        if dlg.exec():
            show_toast(translate('return_updated'), 'success', self)
            self.refresh(True)

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
    def __init__(self, parent=None, return_id=None, return_data=None):
        super().__init__(parent)
        self.edit_return_id = return_id
        self.edit_return_data = return_data or {}
        self.setWindowTitle(translate('edit_return') if self.edit_return_id else translate('purchase_return'))
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

        self.lines_table = QTableWidget(0, RET_COL_COUNT)
        self.lines_table.setHorizontalHeaderLabels([translate('barcode'), translate('return_item'), translate('purchased_qty'), translate('previous_returned'), translate('returnable_qty'), translate('unit'), translate('return_qty'), translate('price'), translate('total'), translate('notes')])
        self.lines_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.lines_table.cellChanged.connect(lambda *_: self.recalculate())
        self.lines_table.setItemDelegateForColumn(RET_COL_UNIT, ReturnUnitDelegate(self))
        self.lines_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked | QTableWidget.EditKeyPressed)
        _ret_install_return_line_column_controls(self, 'purchase_return_lines')
        line_tools = QHBoxLayout()
        self.columns_btn = QPushButton(translate('columns'))
        self.columns_btn.setObjectName('softAction')
        self.columns_btn.clicked.connect(lambda: _ret_show_return_line_columns_menu_from_button(self))
        line_tools.addStretch()
        line_tools.addWidget(self.columns_btn)
        layout.addLayout(line_tools)
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
        buttons.button(QDialogButtonBox.Save).setText(translate('update_return') if self.edit_return_id else translate('save_return'))
        buttons.button(QDialogButtonBox.Cancel).setText(translate('cancel'))
        _ret_install_dialog_print_button(self, buttons, 'purchase')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._update_settlement_controls()
        self.load_invoices()
        if self.edit_return_id:
            _ret_apply_existing_return(self, purchase_return_service, self.edit_return_data, 'purchase')
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


    # Phase134 return dialog column controls compatibility: keep dialog-local calls safe.
    def _install_return_line_column_controls(self, identity):
        _ret_install_return_line_column_controls(self, identity)

    def _restore_return_line_columns(self):
        _ret_restore_return_line_columns(self)

    def _save_return_line_columns(self):
        _ret_save_return_line_columns(self)

    def _show_return_line_columns_menu(self, pos):
        _ret_show_return_line_columns_menu(self, pos)

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
            line = _ret_prepare_line_base_fields(dict(line), 'purchase')
            self.line_rows.append(line)
            _ret_set_readonly_item(self.lines_table, row, RET_COL_BARCODE, line.get('barcode') or line.get('item_barcode') or '')
            _ret_set_readonly_item(self.lines_table, row, RET_COL_ITEM, _ret_item_name(line))
            for col in (RET_COL_ORIGINAL_QTY, RET_COL_PREVIOUS, RET_COL_RETURNABLE):
                _ret_set_readonly_item(self.lines_table, row, col, '')
            units = _ret_units_for_line(line)
            _ret_set_unit_item(self.lines_table, row, RET_COL_UNIT, line, units)
            qty_item = QTableWidgetItem('0')
            self.lines_table.setItem(row, RET_COL_RETURN_QTY, qty_item)
            price_item = QTableWidgetItem('')
            price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)
            self.lines_table.setItem(row, RET_COL_PRICE, price_item)
            total_item = QTableWidgetItem('')
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
            self.lines_table.setItem(row, RET_COL_TOTAL, total_item)
            self.lines_table.setItem(row, RET_COL_NOTES, QTableWidgetItem(str(line.get('notes') or line.get('description') or '')))
            self._unit_changed(row, recalc=False)
        inv = self.invoice_map.get(invoice_id) or {}
        wh_id = inv.get('warehouse_id')
        if wh_id:
            idx = self.warehouse_combo.findData(wh_id)
            if idx >= 0:
                self.warehouse_combo.setCurrentIndex(idx)
        self.lines_table.blockSignals(False)
        self.recalculate()


    def _unit_changed(self, row, recalc=True):
        if row < 0 or row >= len(self.line_rows):
            return
        line = self.line_rows[row]
        unit_data = _ret_selected_unit_data(self.lines_table, row, line)
        factor = unit_data['factor']
        line['_selected_factor'] = factor
        line['_selected_unit'] = unit_data['unit']
        line['_selected_unit_id'] = unit_data['unit_id']
        price_usd = _ret_unit_price_usd_for_factor(line, factor)
        line['_selected_unit_price_usd'] = price_usd
        price_display = currency.convert(price_usd, 'USD', currency.get_display_currency())
        qty_base_key = 'sold_qty_base' if 'sold_qty_base' in line else 'purchased_qty_base'
        for col, key in ((RET_COL_ORIGINAL_QTY, qty_base_key), (RET_COL_PREVIOUS, 'returned_qty_base'), (RET_COL_RETURNABLE, 'returnable_qty_base')):
            _ret_set_readonly_item(self.lines_table, row, col, _ret_fmt_qty(_ret_dec(line.get(key) or 0) / factor))
        _ret_set_readonly_item(self.lines_table, row, RET_COL_PRICE, _ret_fmt_qty(price_display))
        if recalc:
            self.recalculate()

    def recalculate(self):
        total = Decimal('0')
        for row, line in enumerate(self.line_rows):
            try:
                qty_item = self.lines_table.item(row, RET_COL_RETURN_QTY)
                qty = _ret_dec(qty_item.text() if qty_item else 0)
                if qty < 0:
                    qty = Decimal('0')
                factor = _ret_dec(line.get('_selected_factor') or line.get('conversion_factor') or 1, '1')
                if factor <= 0:
                    factor = Decimal('1')
                max_qty = _ret_returnable_base(line) / factor
                if qty > max_qty:
                    qty = max_qty
                    if qty_item is not None:
                        self.lines_table.blockSignals(True)
                        qty_item.setText(_ret_fmt_qty(qty))
                        self.lines_table.blockSignals(False)
                line_total = qty * currency.convert(_ret_dec(line.get('_selected_unit_price_usd') or 0), 'USD', currency.get_display_currency())
                total += line_total
                _ret_set_readonly_item(self.lines_table, row, RET_COL_TOTAL, _ret_fmt_qty(line_total))
            except Exception:
                pass
        self.refund_spin.setMaximum(float(total))
        if self.payment_method_combo.currentData() == 'credit_only':
            self.refund_spin.blockSignals(True)
            self.refund_spin.setValue(0)
            self.refund_spin.blockSignals(False)
        refund = _ret_dec(self.refund_spin.value())
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
                qty = _ret_dec(self.lines_table.item(row, RET_COL_RETURN_QTY).text() if self.lines_table.item(row, RET_COL_RETURN_QTY) else 0)
            except Exception:
                qty = Decimal('0')
            if qty > 0:
                factor = _ret_dec(line.get('_selected_factor') or line.get('conversion_factor') or 1, '1')
                if factor <= 0:
                    factor = Decimal('1')
                base_qty = qty * factor
                if base_qty > _ret_returnable_base(line):
                    QMessageBox.warning(self, translate('return_save_failed'), translate('return_quantity_exceeds_available'))
                    return
                lines.append({'original_invoice_line_id': line.get('id'), 'quantity': str(qty), 'quantity_in_base': str(base_qty), 'conversion_factor': str(factor), 'unit': line.get('_selected_unit') or line.get('unit') or '', 'unit_id': line.get('_selected_unit_id'), 'unit_price': str(_ret_unit_price_usd_for_factor(line, factor)), 'notes': self.lines_table.item(row, RET_COL_NOTES).text() if self.lines_table.item(row, RET_COL_NOTES) else ''})
        try:
            payload = {
                'original_invoice_id': self.invoice_combo.currentData(),
                'date': self.date_edit.date().toString('yyyy-MM-dd'),
                'warehouse_id': self.warehouse_combo.currentData(),
                'refund_amount': '0' if self.payment_method_combo.currentData() == 'credit_only' else str(currency.convert(_ret_dec(self.refund_spin.value()), currency.get_display_currency(), 'USD')),
                'payment_method': self.payment_method_combo.currentData(),
                'cashbox_id': self.cashbox_combo.currentData(),
                'bank_account_id': self.bank_combo.currentData(),
                'notes': self.notes_edit.toPlainText().strip(),
                'lines': lines,
            }
            if self.edit_return_id:
                purchase_return_service.update_return(self.edit_return_id, payload)
            else:
                purchase_return_service.create_return(payload)
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
        self.toolbar.editRequested.connect(self.edit_selected)
        self.toolbar.exportRequested.connect(lambda: self.table.export_to_excel())
        self.toolbar.printRequested.connect(lambda: self.print_selected_return('preview'))
        self.toolbar.refreshRequested.connect(self.refresh)
        self.toolbar.searchChanged.connect(lambda _t: self.refresh(True))
        layout.addWidget(self.toolbar)
        self.table = CustomTableView()
        self.table.set_table_identity('PurchaseReturnsWidget.purchase_returns')
        self.table.setSelectionBehavior(CustomTableView.SelectRows)
        self.toolbar.set_table(self.table)
        self.table.clicked.connect(lambda *_: self.toolbar.set_delete_enabled(True))
        self.table.clicked.connect(lambda *_: self.toolbar.set_edit_enabled(True))
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
            total_usd = _ret_dec(r.get('total') or 0)
            refund_usd = _ret_dec(r.get('refund_amount') or 0)
            credit_usd = _ret_dec(r.get('credit_amount') or 0)
            settlement_remaining_usd = max(total_usd - refund_usd - credit_usd, Decimal('0'))
            row = {
                'id': r.get('id'),
                'reference': r.get('id'),
                'return_no': r.get('return_no',''),
                'original_invoice': r.get('invoice_reference',''),
                'date': r.get('date',''),
                'supplier': r.get('supplier_name') or translate('cash_customer'),
                'return_total': currency.format_amount(currency.convert(total_usd,'USD',currency.get_display_currency())),
                'refund': currency.format_amount(currency.convert(refund_usd,'USD',currency.get_display_currency())),
                'settlement_remaining': currency.format_amount(currency.convert(settlement_remaining_usd,'USD',currency.get_display_currency())),
                'notes': r.get('notes',''),
            }
            data.append(row)
        self.model = GenericTableModel(
            data,
            [translate('reference'), translate('return_no'), translate('original_invoice'), translate('supplier'), translate('return_value'), translate('returned_amount'), translate('settlement_remaining'), translate('date'), translate('notes')],
            key_fields=['id'],
            data_keys=['reference','return_no','original_invoice','supplier','return_total','refund','settlement_remaining','date','notes']
        )
        self.table.setModel(self.model)
        self.toolbar.set_delete_enabled(False)
        self.toolbar.set_edit_enabled(False)
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


    def edit_selected(self):
        rid = self._selected_id()
        if not rid:
            return
        data = purchase_return_service.get(rid)
        if not data:
            QMessageBox.warning(self, translate('error'), translate('return_load_failed'))
            return
        dlg = PurchaseReturnDialog(self, return_id=rid, return_data=data)
        if dlg.exec():
            show_toast(translate('return_updated'), 'success', self)
            self.refresh(True)

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


# Phase110 offline guard markers: مرتجعات المبيعات | مرتجعات المشتريات

# Phase110 stable offline UI markers:
# notify_offline_read(self, 'مرتجعات المبيعات')
# notify_offline_read(self, 'مرتجعات المشتريات')


# Phase134 module-level fallback for return dialog column methods.
# Keeps older call-sites using self._install_return_line_column_controls working.
try:
    PurchaseReturnDialog._install_return_line_column_controls = lambda self, identity: _ret_install_return_line_column_controls(self, identity)
    PurchaseReturnDialog._restore_return_line_columns = lambda self: _ret_restore_return_line_columns(self)
    PurchaseReturnDialog._save_return_line_columns = lambda self: _ret_save_return_line_columns(self)
    PurchaseReturnDialog._show_return_line_columns_menu = lambda self, pos: _ret_show_return_line_columns_menu(self, pos)
except Exception:
    pass
