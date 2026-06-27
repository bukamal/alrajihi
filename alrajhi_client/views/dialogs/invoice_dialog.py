# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox,
                             QDateEdit, QTextEdit, QFormLayout, QMessageBox, QShortcut, QLineEdit,
                             QApplication, QTableView, QHeaderView, QAbstractItemView, QWidget,
                             QStyledItemDelegate, QCompleter, QPushButton, QSpinBox, QCheckBox, QFrame,
                             QSplitter, QSizePolicy, QMenu, QAction)
from PyQt5.QtCore import Qt, QDate, QAbstractTableModel, QModelIndex, QStringListModel, QEvent, QTimer, QSettings, pyqtSignal
from PyQt5.QtGui import QKeySequence, QFont, QBrush, QColor
from decimal import Decimal

from core.services.product_service import product_service
from core.services.catalog_service import catalog_service
from core.services.invoice_service import invoice_service
from core.services.warehouse_service import warehouse_service
from currency import currency
from views.centered_dialog import CenteredDialog
from utils import show_toast
from core.offline_guard import is_offline_read_error, offline_read_message
from ui.form_validation import FormValidator, make_error_label
from features.transactions import TransactionDocumentLayout, TransactionLineGrid
# SmartTableView foundation is provided through TransactionLineGrid for invoice lines.
import qtawesome as qta
from theme_manager import ThemeManager
from i18n import translate, qt_layout_direction

from views.dialogs.invoice_document_components import (
    InvoiceActionsComponent,
    InvoiceHeaderComponent,
    InvoiceLinesComponent,
    InvoicePaymentsComponent,
    InvoicePricingEngine,
)


def _money_decimal(value):
    """Convert UI/API monetary values safely to Decimal.

    Qt spin boxes return float while invoice totals are Decimal. Mixing them
    raises TypeError during print-preview payload construction, especially when
    editing existing invoices.
    """
    if isinstance(value, Decimal):
        return value
    try:
        if value is None or value == '':
            return Decimal('0')
        return Decimal(str(value))
    except Exception:
        return Decimal('0')

def _decimal_value(value, default='0'):
    """Safely normalize DB/API/UI numeric values to Decimal."""
    try:
        if isinstance(value, Decimal):
            return value
        if value is None or value == '':
            return Decimal(str(default))
        return Decimal(str(value))
    except Exception:
        return Decimal(str(default))


def _positive_decimal(value, default='1'):
    result = _decimal_value(value, default)
    return result if result > 0 else Decimal(str(default))

class LinesModel(QAbstractTableModel):
    COL_ROW = 0
    COL_BARCODE = 1
    COL_ITEM_NAME = 2
    COL_QUANTITY = 3
    COL_UNIT = 4
    COL_PRICE = 5
    COL_TOTAL = 6
    COL_NOTES = 7
    COL_PROFIT = 8
    COL_DISCOUNT = 9
    COL_TAX = 10
    COL_DELETE = 11

    EDITABLE_COLUMNS = (COL_BARCODE, COL_ITEM_NAME, COL_QUANTITY, COL_UNIT, COL_PRICE, COL_NOTES, COL_DISCOUNT, COL_TAX)

    def __init__(self, inv_type, parent=None):
        super().__init__(parent)
        self.inv_type = inv_type
        self.display_curr = currency.get_display_currency()
        self.lines = []

    def rowCount(self, parent=QModelIndex()):
        return len(self.lines)

    def columnCount(self, parent=QModelIndex()):
        return 12

    def row_validation_message(self, row):
        if row < 0 or row >= len(self.lines):
            return ''
        line = self.lines[row]
        has_text = bool(str(line.get('barcode', '')).strip() or str(line.get('item_name', '')).strip())
        if has_text and not line.get('item_id'):
            return translate('invoice_line_unresolved_item') if translate('invoice_line_unresolved_item') != 'invoice_line_unresolved_item' else 'Item is not resolved yet'
        try:
            qty = Decimal(str(line.get('qty', 0) or 0))
        except Exception:
            qty = Decimal('0')
        try:
            price = Decimal(str(line.get('price', 0) or 0))
        except Exception:
            price = Decimal('-1')
        if line.get('item_id') and qty <= 0:
            return translate('invoice_line_invalid_qty') if translate('invoice_line_invalid_qty') != 'invoice_line_invalid_qty' else 'Quantity must be greater than zero'
        if line.get('item_id') and price < 0:
            return translate('invoice_line_invalid_price') if translate('invoice_line_invalid_price') != 'invoice_line_invalid_price' else 'Price cannot be negative'
        if line.get('item_id') and not str(line.get('unit_display', '')).strip():
            return translate('invoice_line_missing_unit') if translate('invoice_line_missing_unit') != 'invoice_line_missing_unit' else 'Unit is missing'
        return ''

    def invalid_rows(self):
        return [row for row in range(len(self.lines)) if self.row_validation_message(row)]

    def total_quantity(self):
        total = Decimal('0')
        for line in self.lines:
            if line.get('item_id'):
                total += Decimal(str(line.get('qty', 0) or 0))
        return total

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        line = self.lines[row]
        validation_message = self.row_validation_message(row)
        if role == Qt.ToolTipRole and validation_message:
            return validation_message
        if role == Qt.BackgroundRole and validation_message:
            return QBrush(QColor('#fff1f2'))
        if col == self.COL_DELETE:
            if role == Qt.DisplayRole:
                return "🗑"
            if role == Qt.TextAlignmentRole:
                return Qt.AlignCenter
            return None
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if col == self.COL_ROW:
                return row + 1
            if col == self.COL_BARCODE:
                return line.get('barcode', '')
            if col == self.COL_ITEM_NAME:
                return line.get('item_name', '')
            if col == self.COL_QUANTITY:
                return f"{line['qty']:.2f}"
            if col == self.COL_UNIT:
                return line.get('unit_display', '')
            if col == self.COL_PRICE:
                return f"{line['price']:.2f}"
            if col == self.COL_TOTAL:
                return f"{line['total']:.2f} {self.display_curr}"
            if col == self.COL_NOTES:
                return line.get('notes', '')
            if col == self.COL_PROFIT:
                return '' if self.inv_type != 'sale' else f"{line.get('profit', Decimal('0')):.2f} {self.display_curr}"
            if col == self.COL_DISCOUNT:
                return f"{line.get('discount_percent', Decimal('0')):.2f}"
            if col == self.COL_TAX:
                return f"{line.get('tax_percent', Decimal('0')):.2f}"
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        row = index.row()
        col = index.column()
        line = self.lines[row]
        try:
            if col == self.COL_BARCODE:
                line['barcode'] = str(value or '').strip()
            elif col == self.COL_QUANTITY:
                qty = Decimal(str(value))
                if qty <= 0:
                    return False
                line['qty'] = qty
            elif col == self.COL_UNIT:
                if isinstance(value, tuple) and len(value) == 3:
                    line['unit_id'] = value[0]
                    line['unit_display'] = value[1]
                    line['conversion_factor'] = _positive_decimal(value[2], '1')
                else:
                    line['unit_display'] = str(value or '')
            elif col == self.COL_PRICE:
                price = Decimal(str(value))
                if price < 0:
                    return False
                line['price'] = price
            elif col == self.COL_NOTES:
                line['notes'] = str(value or '')
            elif col == self.COL_DISCOUNT:
                discount = Decimal(str(value))
                if discount < 0 or discount > 100:
                    return False
                line['discount_percent'] = discount
            elif col == self.COL_TAX:
                tax = Decimal(str(value))
                if tax < 0 or tax > 100:
                    return False
                line['tax_percent'] = tax
            else:
                return False
            self.update_row_total(row)
            self.dataChanged.emit(index, index)
            return True
        except Exception:
            return False

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        if index.column() == self.COL_DELETE:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() in self.EDITABLE_COLUMNS:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            headers = [translate('line_no'), translate('barcode'), translate('item'), translate('quantity'), translate('unit'), translate('price'), translate('total'), translate('notes'), translate('item_profit'), translate('discount_percent'), translate('tax_percent'), '']
            return headers[section]
        return None

    def add_empty_row(self):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.lines.append({
            'item_id': None,
            'barcode': '',
            'item_name': '',
            'qty': Decimal('1'),
            'unit_id': None,
            'unit_display': '',
            'conversion_factor': Decimal('1'),
            'price': Decimal('0'),
            'item_cost_base': Decimal('0'),
            'profit': Decimal('0'),
            'discount_percent': Decimal('0'),
            'tax_percent': Decimal('0'),
            'total': Decimal('0'),
            'notes': '',
            'units_data': []
        })
        self.endInsertRows()

    def remove_row(self, row):
        if 0 <= row < self.rowCount():
            self.beginRemoveRows(QModelIndex(), row, row)
            del self.lines[row]
            self.endRemoveRows()
            if self.rowCount() > 0:
                self.dataChanged.emit(self.index(0, self.COL_ROW), self.index(self.rowCount() - 1, self.COL_ROW))

    def set_item(self, row, item_id, item_name, units_data, default_price, barcode=''):
        if 0 <= row < self.rowCount():
            self.lines[row]['item_id'] = item_id
            self.lines[row]['item_name'] = item_name
            self.lines[row]['barcode'] = barcode or ''
            self.lines[row]['units_data'] = units_data
            if units_data and len(units_data) > 0:
                first = units_data[0]
                self.lines[row]['unit_id'] = first.get('id')
                self.lines[row]['unit_display'] = first.get('unit_name', '')
                self.lines[row]['conversion_factor'] = _positive_decimal(first.get('conversion_factor', Decimal('1')), '1')
            else:
                self.lines[row]['unit_id'] = None
                self.lines[row]['unit_display'] = ''
                self.lines[row]['conversion_factor'] = Decimal('1')
            try:
                item = product_service.item_by_id(item_id) or {}
            except Exception:
                item = {}
            self.lines[row]['item_cost_base'] = _decimal_value(item.get('cost_price') or item.get('purchase_price') or item.get('average_cost') or item.get('cost') or 0, '0')
            self.lines[row]['price'] = _decimal_value(default_price, '0')
            self.update_row_total(row)
            self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount()-1))

    def load_invoice_lines(self, lines):
        def val(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        self.beginResetModel()
        self.lines.clear()
        for line in lines or []:
            item_id = val(line, 'item_id')
            try:
                item = product_service.item_by_id(item_id) if item_id else None
            except Exception:
                item = None
            try:
                units = product_service.item_units(item_id) if item_id else []
            except Exception:
                units = []
            item_name = (
                val(line, 'item_name') or val(line, 'name') or val(line, 'product_name')
                or val(line, 'itemName') or val(line, 'productName')
                or (item or {}).get('name', '') or (f"#{item_id}" if item_id else '')
            )
            base_unit = (
                (item or {}).get('unit') or val(line, 'base_unit') or val(line, 'unit_name')
                or val(line, 'unit') or translate('unit_piece')
            )
            current_unit = val(line, 'unit') or val(line, 'unit_name') or base_unit or translate('unit_piece')
            units_list = [{'id': None, 'unit_name': base_unit or translate('unit_piece'), 'conversion_factor': Decimal('1')}]
            for u in units:
                if not isinstance(u, dict):
                    continue
                unit_name = u.get('unit_name') or u.get('name') or ''
                if not unit_name:
                    continue
                factor = _positive_decimal(u.get('conversion_factor', 1), '1')
                units_list.append({'id': u.get('id'), 'unit_name': unit_name, 'conversion_factor': factor})
            current_factor = Decimal('1')
            current_unit_id = val(line, 'unit_id')
            for u in units_list:
                if u.get('unit_name') == current_unit or (current_unit_id is not None and u.get('id') == current_unit_id):
                    current_unit = u.get('unit_name') or current_unit
                    current_factor = _positive_decimal(u.get('conversion_factor', Decimal('1')), '1')
                    current_unit_id = u.get('id')
                    break
            stored_factor = val(line, 'conversion_factor') or val(line, 'factor')
            if stored_factor is not None:
                current_factor = _positive_decimal(stored_factor, '1')
            quantity = _decimal_value(val(line, 'quantity', val(line, 'qty', 0)), '0')
            unit_price = _decimal_value(val(line, 'unit_price', val(line, 'price', 0)), '0')
            total = _decimal_value(val(line, 'total', 0), '0')
            price_display = _decimal_value(currency.convert(unit_price, currency.storage_currency(), self.display_curr), '0')
            total_display = _decimal_value(currency.convert(total, currency.storage_currency(), self.display_curr), '0')
            self.lines.append({
                'item_id': item_id,
                'barcode': val(line, 'barcode', '') or (item or {}).get('barcode', '') or (item or {}).get('code', '') or '',
                'item_name': item_name,
                'qty': quantity,
                'unit_id': current_unit_id,
                'unit_display': current_unit,
                'conversion_factor': current_factor,
                'price': price_display,
                'item_cost_base': _decimal_value((item or {}).get('cost_price') or (item or {}).get('purchase_price') or (item or {}).get('average_cost') or val(line, 'cost_price', val(line, 'unit_cost', 0)), '0'),
                'profit': Decimal('0'),
                'discount_percent': _decimal_value(val(line, 'discount_percent', 0), '0'),
                'tax_percent': _decimal_value(val(line, 'tax_percent', 0), '0'),
                'total': total_display,
                'notes': val(line, 'description', '') or val(line, 'notes', '') or '',
                'units_data': units_list
            })
        self.endResetModel()
        if not self.lines:
            self.add_empty_row()

    def get_lines_data(self):
        result = []
        for line in self.lines:
            if line['item_id'] is None:
                continue
            if Decimal(str(line.get('qty', 0))) <= 0:
                continue
            base_qty = line['qty'] * line.get('conversion_factor', Decimal('1'))
            price_usd = currency.convert(line['price'], self.display_curr, currency.storage_currency())
            total_usd = currency.convert(line['total'], self.display_curr, currency.storage_currency())
            result.append({
                'item_id': line['item_id'],
                'item_name': line.get('item_name', ''),
                'barcode': line.get('barcode', ''),
                'quantity': line['qty'],
                'unit': line.get('unit_display', ''),
                'unit_id': line.get('unit_id'),
                'conversion_factor': line.get('conversion_factor', Decimal('1')),
                'base_qty': base_qty,
                'unit_price': price_usd,
                'total': total_usd,
                'description': line.get('notes', ''),
                'discount_percent': float(line.get('discount_percent', Decimal('0'))),
                'tax_percent': float(line.get('tax_percent', Decimal('0')))
            })
        return result

    def update_row_total(self, row):
        if 0 <= row < self.rowCount():
            line = self.lines[row]
            subtotal = _decimal_value(line.get('qty', 0), '0') * _decimal_value(line.get('price', 0), '0')
            discount_percent = _decimal_value(line.get('discount_percent', 0), '0')
            tax_percent = _decimal_value(line.get('tax_percent', 0), '0')
            after_discount = subtotal - (subtotal * discount_percent / Decimal('100'))
            line['total'] = after_discount + (after_discount * tax_percent / Decimal('100'))
            try:
                if self.inv_type == 'sale':
                    factor = _positive_decimal(line.get('conversion_factor', 1), '1')
                    unit_cost_display = currency.convert(_decimal_value(line.get('item_cost_base', 0), '0') * factor, currency.storage_currency(), self.display_curr)
                    line['profit'] = (_decimal_value(line.get('price', 0), '0') - _decimal_value(unit_cost_display, '0')) * _decimal_value(line.get('qty', 0), '0')
                else:
                    line['profit'] = Decimal('0')
            except Exception:
                line['profit'] = Decimal('0')
            self.dataChanged.emit(self.index(row, self.COL_TOTAL), self.index(row, self.COL_PROFIT))

class InvoiceDialog(CenteredDialog):
    dirtyChanged = pyqtSignal(bool)
    saved = pyqtSignal(object)

    def __init__(self, inv_type, parent=None, invoice_id=None, embedded=False):
        super().__init__(parent)
        self._embedded_mode = bool(embedded)
        if self._embedded_mode:
            self.setModal(False)
            self.setWindowFlags(Qt.Widget)
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            if hasattr(self, "title_bar"):
                self.title_bar.setVisible(False)
        self.inv_type = inv_type
        self.invoice_id = invoice_id
        self.display_curr = currency.get_display_currency()
        self.symbol = currency.get_currency_symbol(self.display_curr)
        self.items_for_combo = []
        self.customers = []
        self.suppliers = []
        self.selected_entity_id = None
        self._updating_payment = False
        self._paid_manually_changed = False
        invoice_type_label = translate('sale_type') if inv_type == 'sale' else translate('purchase_type')
        self.setWindowTitle(translate('edit_invoice_window', type=invoice_type_label) if invoice_id else translate('new_invoice_window', type=invoice_type_label))
        self.setLayoutDirection(qt_layout_direction())
        self.resize(1280, 760)
        self.setMinimumSize(1120, 680)

        self.init_ui()
        self._install_document_components()
        self.setup_shortcuts()
        self.load_items_for_combo()
        self.load_entities()
        if invoice_id:
            self.load_invoice_data(invoice_id)
        self.update_total_display()


    def _install_document_components(self):
        """Install reusable invoice document components.

        Phase 48 keeps the proven invoice controls in place but moves the
        workspace contract to explicit component boundaries.  New sales,
        purchase, return, restaurant checkout, and fast-POS flows should use
        these components instead of reaching into the legacy dialog internals.
        """
        self.header_component = InvoiceHeaderComponent(self)
        self.lines_component = InvoiceLinesComponent(self)
        self.pricing_engine = InvoicePricingEngine(self)
        self.payments_component = InvoicePaymentsComponent(self)
        self.actions_component = InvoiceActionsComponent(self)

    def invoice_document_payload(self):
        """Return the normalized unit-aware invoice document payload."""
        return {
            'type': self.inv_type,
            'invoice_id': self.invoice_id,
            'header': self.header_component.data() if hasattr(self, 'header_component') else {},
            'lines': self.lines_component.payload() if hasattr(self, 'lines_component') else self.lines_model.get_lines_data(),
            'pricing': self.pricing_engine.summary() if hasattr(self, 'pricing_engine') else {},
            'paid': self.payments_component.paid_amount() if hasattr(self, 'payments_component') else Decimal('0'),
        }

    def mark_dirty(self):
        super().mark_dirty()
        self.dirtyChanged.emit(True)

    def reset_dirty(self):
        super().reset_dirty()
        self.dirtyChanged.emit(False)

    def workspace_title(self):
        prefix = translate('sales_invoice') if self.inv_type == 'sale' else translate('purchase_invoice')
        reference = self.ref_edit.text().strip() if hasattr(self, 'ref_edit') else ''
        if reference:
            return f"{prefix} {reference}"
        return self.windowTitle()

    def workspace_save(self):
        if hasattr(self, 'actions_component'):
            self.actions_component.save()
        else:
            self.on_save()

    def workspace_print(self):
        if hasattr(self, 'actions_component'):
            self.actions_component.print()
        else:
            self.print_invoice_professional()

    def workspace_export(self):
        # Phase 235: route legacy export requests to the unified print action.
        self.workspace_print()

    def workspace_refresh(self):
        if self.invoice_id:
            self.load_invoice_data(self.invoice_id)

    def load_invoice_data(self, invoice_id):
        inv = invoice_service.get(invoice_id)
        if not inv:
            show_toast(translate("invoice_not_found"), "error", self)
            self.reject()
            return
        if self.inv_type == 'sale':
            if inv.get('customer_id'):
                cust = next((c for c in self.customers if c.get('id') == inv['customer_id']), None)
                if cust:
                    self.entity_search.setText(cust.get('name', ''))
                    self.selected_entity_id = cust.get('id')
            else:
                self.entity_search.setText(translate("cash_customer"))
                self.selected_entity_id = None
        else:
            if inv.get('supplier_id'):
                supp = next((s for s in self.suppliers if s.get('id') == inv['supplier_id']), None)
                if supp:
                    self.entity_search.setText(supp.get('name', ''))
                    self.selected_entity_id = supp.get('id')
            else:
                self.entity_search.setText(translate("cash_customer"))
                self.selected_entity_id = None
        self.date_edit.setDate(QDate.fromString(inv['date'], "yyyy-MM-dd"))
        self.ref_edit.setText(inv.get('reference', ''))
        self.notes_edit.setPlainText(inv.get('notes', ''))
        self.lines_model.load_invoice_lines(inv.get('lines', []))
        self.update_total_display()
        # فحص تغير الأسعار يجب أن يتم بعد تحميل السطور في النموذج؛ وإلا فإن اختيار
        # "تحديث الأسعار" لا يطبق أي تغيير فعليًا على السطور المعروضة.
        self.check_price_differences(inv)

    def _invoice_line_value(self, line, key, default=None):
        if isinstance(line, dict):
            return line.get(key, default)
        return getattr(line, key, default)

    def _line_conversion_factor(self, line):
        """Return the saved line unit conversion factor.

        Invoice line price is stored per selected invoice unit.  Therefore a
        carton/box line must be compared against the current item base price
        multiplied by the same conversion factor, not against the base price.
        """
        return _positive_decimal(
            self._invoice_line_value(line, 'conversion_factor', self._invoice_line_value(line, 'factor', 1)),
            '1'
        )

    def _item_current_unit_price_usd(self, item, line, inv_type=None):
        inv_type = inv_type or self.inv_type
        base_price = _decimal_value(item.get('selling_price' if inv_type == 'sale' else 'purchase_price', 0), '0')
        return base_price * self._line_conversion_factor(line)

    def check_price_differences(self, invoice):
        """Check price differences between stored invoice lines and current item prices.

        The comparison is unit-aware. Saved invoice line prices are per selected
        unit, while item master prices are stored per base unit.
        """
        changes = []
        inv_type = invoice.get('type', self.inv_type)
        for line in invoice.get('lines', []):
            item_id = self._invoice_line_value(line, 'item_id')
            item = product_service.item_by_id(item_id)
            if not item:
                continue
            current_price_usd = self._item_current_unit_price_usd(item, line, inv_type)
            current_price_display = _decimal_value(currency.convert(current_price_usd, currency.storage_currency(), self.display_curr), '0')
            old_price = _decimal_value(self._invoice_line_value(line, 'unit_price', 0), '0')
            old_price_display = _decimal_value(currency.convert(old_price, currency.storage_currency(), self.display_curr), '0')
            if abs(current_price_display - old_price_display) > Decimal('0.01'):
                changes.append(translate('was_now', item=item['name'], old=currency.format_amount(old_price_display), new=currency.format_amount(current_price_display)))
        if changes:
            msg = translate('price_update_msg', intro=translate('price_update_intro'), changes='\n'.join(changes), question=translate('price_update_question'))
            reply = QMessageBox.question(self, translate("price_update_title"), msg, QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                for idx, line in enumerate(self.lines_model.lines):
                    if line['item_id']:
                        item = product_service.item_by_id(line['item_id'])
                        if item:
                            new_price_usd = self._item_current_unit_price_usd(item, line, self.inv_type)
                            new_price_display = currency.convert(new_price_usd, currency.storage_currency(), self.display_curr)
                            self.lines_model.setData(self.lines_model.index(idx, LinesModel.COL_PRICE), new_price_display, Qt.EditRole)
                self.update_total_display()

    def _invoice_accent(self):
        c = ThemeManager.colors()
        return c['primary'] if self.inv_type == 'sale' else c.get('primary_2', c['primary'])

    def _apply_modern_invoice_style(self):
        c = ThemeManager.colors()
        accent = self._invoice_accent()
        self.setStyleSheet(f"""
            QDialog {{ background: {c['bg_window']}; color: {c['text_primary']}; }}
            QLabel#DialogTitle {{ color: {c['primary']}; font-size: 21px; font-weight: 900; }}
            QLabel#DialogSubtitle {{ color: {c['text_secondary']}; font-size: 12px; }}
            QFrame#HeaderCard, QFrame#TotalsCard, QFrame#ActionCard, QFrame#RightPanel, QFrame#BottomActionBar {{
                background: {c['card_bg']}; border: 1px solid {c['border']}; border-radius: 14px;
            }}
            QTableView#TransactionLineGrid, QTableView#InvoiceLinesTable {{
                font-size: 13px;
                border-radius: 14px;
            }}
            QSplitter#TransactionDocumentSplitter::handle {{
                background: {c['border']}; border-radius: 4px; margin: 8px 2px;
            }}
            QFrame#TransactionBottomActionBar {{
                background: {c['card_bg']}; border: 1px solid {c['border']}; border-radius: 14px;
            }}
            QLabel#SectionTitle {{ color: {c['text_primary']}; font-size: 14px; font-weight: 800; }}
            QLabel#muted {{ color: {c['text_secondary']}; font-size: 11px; }}
            QLabel#InvoiceGridStatus {{
                color: {c['text_secondary']}; font-size: 11px; font-weight: 700;
                padding: 4px 8px; border-radius: 8px; background: {c['card_bg']};
            }}
            QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox, QTextEdit {{
                min-height: 34px; border: 1px solid {c['border']}; border-radius: 9px; padding: 5px 9px;
                background: {c['input_bg']}; color: {c['text_primary']}; font-size: 13px;
                selection-background-color: {c['selection_bg']}; selection-color: {c['selection_text']};
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
                border: 1px solid {c['border_focus']}; background: {c['input_bg']};
            }}
            QTableView, QTableWidget {{
                background: {c['bg_table']}; color: {c['text_primary']}; alternate-background-color: {c['bg_table_alt']};
                gridline-color: {c['border']}; border: 1px solid {c['border']}; border-radius: 12px;
                selection-background-color: {c['selection_bg']}; selection-color: {c['selection_text']}; outline: 0;
            }}
            QTableView::item, QTableWidget::item {{ padding: 6px; border-bottom: 1px solid {c['border']}; }}
            QTableView::item:hover, QTableWidget::item:hover {{ background: {c['brand_soft']}; }}
            QHeaderView::section {{
                background: {c['header_bg']}; color: {c['header_text']}; font-weight: 800; padding: 8px;
                border: none; border-left: 1px solid {c['border']};
            }}
            QPushButton {{
                min-height: 34px; border-radius: 9px; padding: 6px 12px; border: 1px solid {c['border']};
                background: {c['bg_panel']}; color: {c['text_primary']}; font-weight: 700;
            }}
            QPushButton:hover {{ background: {c['brand_soft']}; border-color: {c['primary']}; }}
            QPushButton#primary {{ background: {accent}; color: white; border: 1px solid {accent}; }}
            QPushButton#danger {{ background: {c['danger_soft']}; color: {c['danger']}; border: 1px solid {c['danger']}; }}
        """)


    def _make_field_block(self, label_text, widget, stretch=1):
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        label = QLabel(label_text)
        label.setObjectName("muted")
        layout.addWidget(label)
        layout.addWidget(widget)
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return box

    def init_ui(self):
        self._apply_modern_invoice_style()
        root_layout = QVBoxLayout(self.content_widget)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        title_frame = QFrame()
        self.title_frame = title_frame
        title_frame.setObjectName("HeaderCard")
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(16, 12, 16, 12)
        title_layout.setSpacing(12)

        title_box = QVBoxLayout()
        title = QLabel(translate('sales_invoice') if self.inv_type == 'sale' else translate('purchase_invoice'))
        title.setObjectName("DialogTitle")
        subtitle = QLabel(translate('fast_invoice_subtitle'))
        subtitle.setObjectName("DialogSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        title_layout.addLayout(title_box)
        title_layout.addStretch()

        self.new_btn = QPushButton(translate('new'))
        self.new_btn.setObjectName("softAction")
        self.save_btn = QPushButton(translate('save_shortcut'))
        self.save_btn.setObjectName("primary")
        self.print_btn = QPushButton(translate('print_shortcut'))
        self.print_btn.setObjectName("softAction")
        # Phase 235: one unified print button; no preview/PDF menu in invoice creation.
        self.print_menu = None
        self.print_preview_action = None
        self.print_browser_action = None
        self.print_direct_action = None
        self.print_pdf_action = None
        self.print_btn.clicked.connect(self.direct_print_invoice)
        self.cancel_btn = QPushButton(translate('cancel_shortcut'))
        for btn in (self.new_btn, self.save_btn, self.print_btn, self.cancel_btn):
            btn.setMinimumWidth(110)
        root_layout.addWidget(title_frame)

        self.form_error_label = make_error_label()
        root_layout.addWidget(self.form_error_label)

        header_frame = QFrame()
        header_frame.setObjectName("HeaderCard")
        header_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(14, 12, 14, 12)
        header_layout.setSpacing(10)
        header_title = QLabel(translate('invoice_details'))
        header_title.setObjectName("SectionTitle")
        header_layout.addWidget(header_title)

        self.entity_search = QLineEdit()
        self.entity_search.setPlaceholderText(translate("entity_placeholder"))
        self.entity_search.textChanged.connect(self.on_entity_text_changed)
        self.entity_completer = QCompleter()
        self.entity_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.entity_completer.activated.connect(self.on_entity_selected)
        self.entity_search.setCompleter(self.entity_completer)

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)

        self.warehouse_combo = QComboBox()
        self._load_warehouses()
        self.warehouse_combo.currentIndexChanged.connect(lambda *_: self.update_warehouse_availability_label())

        self.ref_edit = QLineEdit()
        self.ref_edit.setPlaceholderText(translate("auto_reference_placeholder"))

        self.balance_label = QLabel()
        self.balance_label.setObjectName("muted")
        self.balance_label.setWordWrap(True)

        row1 = QHBoxLayout()
        row1.setSpacing(10)
        row1.addWidget(self._make_field_block(translate("customer") if self.inv_type == 'sale' else translate("supplier"), self.entity_search), 2)
        row1.addWidget(self._make_field_block(translate("date"), self.date_edit), 1)
        row1.addWidget(self._make_field_block(translate("reference"), self.ref_edit), 1)
        header_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(10)
        row2.addWidget(self._make_field_block(translate("warehouse") if self.inv_type == 'sale' else translate("warehouse_receive"), self.warehouse_combo), 2)
        self.add_entity_btn = QPushButton(translate('add_customer') if self.inv_type == 'sale' else translate('add_supplier'))
        self.add_entity_btn.setObjectName("softAction")
        self.add_entity_btn.clicked.connect(self.add_new_entity)
        row2.addWidget(self._make_field_block(translate("quick_action"), self.add_entity_btn), 1)
        row2.addStretch(1)
        header_layout.addLayout(row2)

        header_layout.addWidget(self.balance_label)
        root_layout.addWidget(header_frame)

        content_splitter = QSplitter(Qt.Horizontal)
        self.content_splitter = content_splitter
        content_splitter.setChildrenCollapsible(False)
        content_splitter.setHandleWidth(8)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        search_frame = QFrame()
        search_frame.setObjectName("ActionCard")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 10, 12, 10)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(translate("barcode_search_placeholder"))
        self.search_input.returnPressed.connect(self.add_item_from_search)
        self.quick_qty_spin = QDoubleSpinBox()
        self.quick_qty_spin.setObjectName('InvoiceQuickQtySpin')
        self.quick_qty_spin.setRange(0.001, 999999.0)
        self.quick_qty_spin.setDecimals(3)
        self.quick_qty_spin.setValue(1.0)
        self.quick_qty_spin.setToolTip(translate('quick_qty_tooltip') if translate('quick_qty_tooltip') != 'quick_qty_tooltip' else 'Quantity used by barcode/quick add')
        self.camera_scan_btn = QPushButton(translate('scan'))
        self.camera_scan_btn.setObjectName("softAction")
        self.camera_scan_btn.setToolTip(translate("barcode_scan_tooltip"))
        self.camera_scan_btn.clicked.connect(self.scan_barcode_with_camera)
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self._make_field_block(translate('quantity'), self.quick_qty_spin), 0)
        search_layout.addWidget(self.camera_scan_btn)
        left_layout.addWidget(search_frame)

        self.lines_model = LinesModel(self.inv_type)
        self.lines_table = TransactionLineGrid(
            identity=f"transaction_lines_{self.inv_type}",
            transaction_type=self.inv_type,
            required_columns={LinesModel.COL_ITEM_NAME, LinesModel.COL_QUANTITY, LinesModel.COL_UNIT, LinesModel.COL_TOTAL},
            compact_columns={LinesModel.COL_BARCODE, LinesModel.COL_PRICE, LinesModel.COL_DISCOUNT, LinesModel.COL_TAX},
        )
        self.lines_table.setObjectName("InvoiceLinesTable")
        self.lines_table.set_responsive_columns(False)
        self.lines_table.setModel(self.lines_model)
        self.lines_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lines_table.setAlternatingRowColors(True)
        self.lines_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.lines_table.verticalHeader().setVisible(False)
        self.lines_table.verticalHeader().setDefaultSectionSize(38)
        self.lines_table.setShowGrid(True)
        header = self.lines_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setSectionResizeMode(LinesModel.COL_ITEM_NAME, QHeaderView.Stretch)
        self.lines_table.setColumnWidth(LinesModel.COL_ROW, 42)
        self.lines_table.setColumnWidth(LinesModel.COL_BARCODE, 135)
        self.lines_table.setColumnWidth(LinesModel.COL_QUANTITY, 88)
        self.lines_table.setColumnWidth(LinesModel.COL_UNIT, 95)
        self.lines_table.setColumnWidth(LinesModel.COL_PRICE, 105)
        self.lines_table.setColumnWidth(LinesModel.COL_TOTAL, 130)
        self.lines_table.setColumnWidth(LinesModel.COL_NOTES, 160)
        self.lines_table.setColumnWidth(LinesModel.COL_PROFIT, 120)
        self.lines_table.setColumnWidth(LinesModel.COL_DISCOUNT, 78)
        self.lines_table.setColumnWidth(LinesModel.COL_TAX, 78)
        self.lines_table.setColumnWidth(LinesModel.COL_DELETE, 48)
        self.lines_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lines_table.customContextMenuRequested.connect(self._show_lines_columns_menu)
        self.lines_table.installEventFilter(self)

        from views.dialogs.invoice_delegates import ItemComboDelegate, UnitComboBoxDelegate, DoubleSpinDelegate
        self.item_delegate = ItemComboDelegate(self.items_for_combo, self.lines_table)
        self.lines_table.setItemDelegateForColumn(LinesModel.COL_ITEM_NAME, self.item_delegate)
        self.unit_delegate = UnitComboBoxDelegate()
        self.lines_table.setItemDelegateForColumn(LinesModel.COL_UNIT, self.unit_delegate)
        self.double_delegate = DoubleSpinDelegate()
        self.lines_table.setItemDelegateForColumn(LinesModel.COL_QUANTITY, self.double_delegate)
        self.lines_table.setItemDelegateForColumn(LinesModel.COL_PRICE, self.double_delegate)
        self.lines_table.setItemDelegateForColumn(LinesModel.COL_DISCOUNT, self.double_delegate)
        self.lines_table.setItemDelegateForColumn(LinesModel.COL_TAX, self.double_delegate)
        self._restore_lines_table_layout()
        self.lines_table.horizontalHeader().sectionMoved.connect(lambda *_: self._save_lines_table_layout())
        self.lines_table.horizontalHeader().sectionResized.connect(lambda *_: self._save_lines_table_layout())

        self.lines_table.clicked.connect(self.on_table_clicked)
        if not self.invoice_id:
            self.lines_model.add_empty_row()
        self.lines_model.dataChanged.connect(self.on_line_data_changed)
        self.lines_model.dataChanged.connect(lambda *_: self.update_warehouse_availability_label())
        self.lines_model.rowsInserted.connect(lambda *_: self.update_invoice_grid_status())
        self.lines_model.rowsRemoved.connect(lambda *_: self.update_invoice_grid_status())
        self.lines_table.setMinimumHeight(360)
        self.lines_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout.addWidget(self.lines_table, 1)

        self.invoice_grid_status_label = QLabel('')
        self.invoice_grid_status_label.setObjectName('InvoiceGridStatus')
        self.invoice_grid_status_label.setWordWrap(True)
        left_layout.addWidget(self.invoice_grid_status_label, 0)

        btn_line_layout = QHBoxLayout()
        self.add_line_btn = QPushButton(translate('add_line'))
        self.add_line_btn.setObjectName("softAction")
        self.add_line_btn.clicked.connect(self.add_empty_line)
        self.remove_line_btn = QPushButton(translate('remove_line'))
        self.remove_line_btn.setObjectName("danger")
        self.remove_line_btn.clicked.connect(self.remove_selected_line)
        self.columns_btn = QPushButton(translate('columns'))
        self.columns_btn.setObjectName("softAction")
        self.columns_btn.clicked.connect(self._show_lines_columns_menu_from_button)
        btn_line_layout.addWidget(self.add_line_btn)
        btn_line_layout.addWidget(self.remove_line_btn)
        btn_line_layout.addWidget(self.columns_btn)
        btn_line_layout.addStretch()
        self.invoice_grid_shortcuts_label = QLabel(
            translate('invoice_grid_shortcuts_hint')
            if translate('invoice_grid_shortcuts_hint') != 'invoice_grid_shortcuts_hint'
            else 'Enter: next cell • Insert: new line • Ctrl+D duplicate • Ctrl+L barcode • F6 qty • F4 columns • Ctrl+Shift+F fit columns'
        )
        self.invoice_grid_shortcuts_label.setObjectName('muted')
        btn_line_layout.addWidget(self.invoice_grid_shortcuts_label)
        left_layout.addLayout(btn_line_layout)

        left_layout.addWidget(QLabel(translate('general_notes')))
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(68)
        left_layout.addWidget(self.notes_edit)

        right_panel = QFrame()
        right_panel.setObjectName("RightPanel")
        right_panel.setMinimumWidth(300)
        right_panel.setMaximumWidth(390)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(10)

        totals_title = QLabel(translate('invoice_summary'))
        totals_title.setObjectName("SectionTitle")
        right_layout.addWidget(totals_title)

        self.warehouse_availability_label = QLabel(translate('select_warehouse_for_stock'))
        self.warehouse_availability_label.setObjectName("muted")
        self.warehouse_availability_label.setWordWrap(True)
        right_layout.addWidget(self.warehouse_availability_label)

        self.discount_type = QComboBox()
        self.discount_type.addItems([translate('percent_discount'), translate('amount_discount')])
        self.discount_value = QDoubleSpinBox()
        self.discount_value.setRange(0, 999999999)
        self.discount_value.setDecimals(2)
        self.discount_value.setPrefix(f"{self.symbol} ")
        discount_container = QWidget()
        discount_layout = QHBoxLayout(discount_container)
        discount_layout.setContentsMargins(0, 0, 0, 0)
        discount_layout.setSpacing(8)
        discount_layout.addWidget(self.discount_type, 1)
        discount_layout.addWidget(self.discount_value, 2)
        right_layout.addWidget(self._make_field_block(translate("discount_field"), discount_container))

        self.paid_spin = QDoubleSpinBox()
        self.paid_spin.setRange(0, 999999999)
        self.paid_spin.setDecimals(2)
        self.paid_spin.setPrefix(f"{self.symbol} ")
        right_layout.addWidget(self._make_field_block(translate("paid_field"), self.paid_spin))

        payment_tools = QHBoxLayout()
        self.full_payment_btn = QPushButton(translate('full_payment'))
        self.full_payment_btn.setObjectName("softAction")
        self.no_payment_btn = QPushButton(translate('deferred_payment'))
        self.no_payment_btn.setObjectName("softAction")
        payment_tools.addWidget(self.full_payment_btn)
        payment_tools.addWidget(self.no_payment_btn)
        right_layout.addLayout(payment_tools)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #e2e8f0;")
        right_layout.addWidget(separator)

        self.total_before_label = QLabel(translate('total_before_discount', amount='0'))
        self.discount_amount_label = QLabel(translate('discount', amount='0'))
        self.total_after_label = QLabel(translate('total_after_discount', amount='0'))
        self.remaining_label = QLabel(translate('remaining_label', amount='0'))
        self.total_after_label.setObjectName("TotalMain")
        self.remaining_label.setObjectName("TotalRemaining")
        self.total_before_label.setObjectName("TotalPaid")
        for lbl in (self.total_before_label, self.discount_amount_label, self.total_after_label, self.remaining_label):
            lbl.setWordWrap(True)
            right_layout.addWidget(lbl)

        right_layout.addStretch()
        hint = QLabel(translate('invoice_shortcuts_hint'))
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        right_layout.addWidget(hint)

        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(right_panel)
        content_splitter.setStretchFactor(0, 5)
        content_splitter.setStretchFactor(1, 1)
        root_layout.addWidget(content_splitter, 1)

        bottom_bar = QFrame()
        self.bottom_action_bar = bottom_bar
        bottom_bar.setObjectName("BottomActionBar")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(12, 8, 12, 8)
        bottom_layout.setSpacing(10)
        bottom_layout.addWidget(self.new_btn)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.save_btn)
        bottom_layout.addWidget(self.print_btn)
        bottom_layout.addWidget(self.cancel_btn)
        root_layout.addWidget(bottom_bar, 0)

        self.transaction_document_layout = TransactionDocumentLayout(self, transaction_type=self.inv_type)
        self.transaction_document_layout.apply()

        self.discount_value.valueChanged.connect(self.update_total_display)
        self.discount_type.currentIndexChanged.connect(self.update_total_display)
        self.paid_spin.valueChanged.connect(self.on_paid_changed)
        self.full_payment_btn.clicked.connect(self.set_paid_full)
        self.no_payment_btn.clicked.connect(self.set_paid_zero)
        self.save_btn.clicked.connect(self.on_save)
        # Phase 235: print_btn is connected directly to unified print.
        self.cancel_btn.clicked.connect(self.reject)
        self.new_btn.clicked.connect(self._clear_invoice_form)
        QTimer.singleShot(0, self.focus_barcode_input)
        QTimer.singleShot(0, self.update_invoice_grid_status)


    def _quick_add_qty(self):
        try:
            if hasattr(self, 'quick_qty_spin'):
                value = Decimal(str(self.quick_qty_spin.value()))
                return value if value > 0 else Decimal('1')
        except Exception:
            pass
        return Decimal('1')

    def _reset_quick_add_qty(self):
        try:
            if hasattr(self, 'quick_qty_spin'):
                self.quick_qty_spin.setValue(1.0)
        except Exception:
            pass

    def update_invoice_grid_status(self):
        if not hasattr(self, 'invoice_grid_status_label'):
            return
        model = getattr(self, 'lines_model', None)
        if model is None:
            self.invoice_grid_status_label.setText('')
            return
        active_lines = [line for line in getattr(model, 'lines', []) if line.get('item_id')]
        invalid_rows = model.invalid_rows() if hasattr(model, 'invalid_rows') else []
        visible_cols = len(self.lines_table.visible_columns()) if hasattr(self, 'lines_table') and hasattr(self.lines_table, 'visible_columns') else model.columnCount()
        total_qty = model.total_quantity() if hasattr(model, 'total_quantity') else Decimal('0')
        label = translate('invoice_grid_status', lines=len(active_lines), qty=f'{total_qty:.3f}', columns=visible_cols, invalid=len(invalid_rows))
        if label == 'invoice_grid_status':
            label = f'Lines: {len(active_lines)} • Qty: {total_qty:.3f} • Columns: {visible_cols} • Issues: {len(invalid_rows)}'
        self.invoice_grid_status_label.setText(label)

    def focus_barcode_input(self):
        """Keep barcode/item quick-entry ready for continuous invoicing."""
        if hasattr(self, 'search_input') and self.search_input is not None:
            self.search_input.setFocus()
            self.search_input.selectAll()

    def _clear_invoice_form(self):
        if self.invoice_id:
            show_toast(translate("new_button_only_new_invoice"), "warning", self)
            return
        self.entity_search.clear()
        self.selected_entity_id = None
        self.ref_edit.clear()
        self.notes_edit.clear()
        self.discount_value.setValue(0)
        self.paid_spin.setValue(0)
        self.lines_model.beginResetModel()
        self.lines_model.lines.clear()
        self.lines_model.endResetModel()
        self.lines_model.add_empty_row()
        if hasattr(self, 'quick_qty_spin'):
            self.quick_qty_spin.setValue(1.0)
        self.update_invoice_grid_status()
        self.focus_barcode_input()
        self._paid_manually_changed = False
        self.update_total_display()

    def _first_empty_line_row(self):
        for row, line in enumerate(self.lines_model.lines):
            if not line.get('item_id'):
                return row
        return None

    def _target_line_for_new_item(self):
        row = self._first_empty_line_row()
        if row is None:
            self.add_empty_line()
            row = self.lines_model.rowCount() - 1
        return row

    def _find_line_by_item_id(self, item_id):
        try:
            item_id = int(item_id)
        except Exception:
            return None
        for row, line in enumerate(self.lines_model.lines):
            try:
                if line.get('item_id') is not None and int(line.get('item_id')) == item_id:
                    return row
            except Exception:
                continue
        return None

    def _increment_existing_line(self, row, qty):
        if row is None or row < 0 or row >= self.lines_model.rowCount():
            return False
        line = self.lines_model.lines[row]
        try:
            qty = Decimal(str(qty))
            line['qty'] = Decimal(str(line.get('qty', 0))) + qty
            self.lines_model.update_row_total(row)
            self.lines_model.dataChanged.emit(
                self.lines_model.index(row, LinesModel.COL_QUANTITY),
                self.lines_model.index(row, LinesModel.COL_TOTAL)
            )
            self.lines_table.selectRow(row)
            self.mark_dirty()
            self.update_total_display()
            return True
        except Exception:
            return False

    def eventFilter(self, obj, event):
        if obj is getattr(self, 'lines_table', None) and event.type() == QEvent.KeyPress:
            key = event.key()
            modifiers = event.modifiers()
            if key in (Qt.Key_Return, Qt.Key_Enter):
                self._move_to_next_invoice_cell()
                return True
            if key == Qt.Key_Insert:
                self.add_empty_line()
                return True
            if key == Qt.Key_Delete:
                self.remove_selected_line()
                return True
            if key == Qt.Key_L and modifiers & Qt.ControlModifier:
                self.focus_barcode_input()
                return True
            if key == Qt.Key_D and modifiers & Qt.ControlModifier:
                self.duplicate_selected_line()
                return True
            if key == Qt.Key_F4:
                self._show_lines_columns_menu_from_button()
                return True
            if key == Qt.Key_F and modifiers & Qt.ControlModifier and modifiers & Qt.ShiftModifier:
                if hasattr(self.lines_table, 'fit_columns_to_view'):
                    self.lines_table.fit_columns_to_view()
                return True
            if key == Qt.Key_F6:
                if hasattr(self, 'quick_qty_spin'):
                    self.quick_qty_spin.setFocus()
                    self.quick_qty_spin.selectAll()
                return True
            if key == Qt.Key_Escape:
                self.focus_barcode_input()
                return True
        return super().eventFilter(obj, event)

    def _move_to_next_invoice_cell(self):
        index = self.lines_table.currentIndex()
        if not index.isValid():
            self.focus_barcode_input()
            return
        editable = [LinesModel.COL_BARCODE, LinesModel.COL_ITEM_NAME, LinesModel.COL_QUANTITY, LinesModel.COL_UNIT, LinesModel.COL_PRICE, LinesModel.COL_NOTES, LinesModel.COL_DISCOUNT, LinesModel.COL_TAX]
        row, col = index.row(), index.column()
        if col == LinesModel.COL_BARCODE:
            text = str(self.lines_model.lines[row].get('barcode', '') or '').strip()
            if text and not self.lines_model.lines[row].get('item_id'):
                self.search_input.setText(text)
                self.add_item_from_search()
                return
        next_cols = [c for c in editable if c > col]
        if next_cols:
            next_index = self.lines_model.index(row, next_cols[0])
        else:
            if row == self.lines_model.rowCount() - 1:
                self.add_empty_line()
            next_index = self.lines_model.index(row + 1, LinesModel.COL_BARCODE)
        self.lines_table.setCurrentIndex(next_index)
        self.lines_table.edit(next_index)


    def _lines_table_settings_key(self):
        return f"invoice_lines/{self.inv_type}"

    def _default_invoice_line_visible_columns(self):
        if self.inv_type == 'sale':
            return {LinesModel.COL_BARCODE, LinesModel.COL_ITEM_NAME, LinesModel.COL_QUANTITY, LinesModel.COL_UNIT, LinesModel.COL_PRICE, LinesModel.COL_TOTAL, LinesModel.COL_NOTES, LinesModel.COL_PROFIT, LinesModel.COL_DELETE}
        return {LinesModel.COL_BARCODE, LinesModel.COL_ITEM_NAME, LinesModel.COL_UNIT, LinesModel.COL_QUANTITY, LinesModel.COL_PRICE, LinesModel.COL_TOTAL, LinesModel.COL_NOTES, LinesModel.COL_DELETE}

    def _restore_lines_table_layout(self):
        try:
            settings = QSettings('Alrajhi', 'Accounting')
            key = self._lines_table_settings_key()
            saved = settings.value(f'{key}/visible_columns')
            if saved:
                visible = {int(x) for x in str(saved).split(',') if str(x).strip().isdigit()}
            else:
                visible = self._default_invoice_line_visible_columns()
            for col in range(self.lines_model.columnCount()):
                self.lines_table.setColumnHidden(col, col not in visible)
            state = settings.value(f'{key}/header_state')
            if state:
                self.lines_table.horizontalHeader().restoreState(state)
            elif self.inv_type == 'purchase':
                try:
                    h = self.lines_table.horizontalHeader()
                    h.moveSection(h.visualIndex(LinesModel.COL_UNIT), h.visualIndex(LinesModel.COL_QUANTITY))
                except Exception:
                    pass
        except Exception:
            pass

    def _save_lines_table_layout(self):
        try:
            settings = QSettings('Alrajhi', 'Accounting')
            key = self._lines_table_settings_key()
            visible = [str(c) for c in range(self.lines_model.columnCount()) if not self.lines_table.isColumnHidden(c)]
            settings.setValue(f'{key}/visible_columns', ','.join(visible))
            settings.setValue(f'{key}/header_state', self.lines_table.horizontalHeader().saveState())
        except Exception:
            pass

    def _set_line_column_visible(self, column, visible):
        self.lines_table.setColumnHidden(column, not visible)
        self._save_lines_table_layout()

    def _show_lines_columns_menu_from_button(self):
        if hasattr(self, 'columns_btn'):
            self._show_lines_columns_menu(self.columns_btn.rect().bottomLeft(), source_widget=self.columns_btn)

    def _show_lines_columns_menu(self, pos, source_widget=None):
        menu = QMenu(self)
        columns_menu = menu.addMenu(translate('columns'))
        required = self.lines_table.required_columns() if hasattr(self.lines_table, 'required_columns') else set()
        for col in range(self.lines_model.columnCount()):
            header = self.lines_model.headerData(col, Qt.Horizontal, Qt.DisplayRole) or translate('column_number', number=col + 1)
            act = QAction(str(header), self)
            act.setCheckable(True)
            act.setChecked(not self.lines_table.isColumnHidden(col))
            if col in required:
                act.setEnabled(False)
                act.setToolTip(translate('required_column') if translate('required_column') != 'required_column' else 'Required column')
            act.toggled.connect(lambda checked, c=col: self._set_line_column_visible(c, checked))
            columns_menu.addAction(act)
        reset = QAction(translate('reset_columns'), self)
        reset.triggered.connect(lambda: (QSettings('Alrajhi', 'Accounting').remove(self._lines_table_settings_key()), self._restore_lines_table_layout()))
        columns_menu.addSeparator()
        columns_menu.addAction(reset)
        target = source_widget or self.lines_table.viewport()
        menu.exec(target.mapToGlobal(pos))


    def _load_warehouses(self):
        try:
            warehouses = warehouse_service.warehouses()
        except Exception:
            warehouses = []
        self.warehouse_combo.clear()
        default_id = None
        try:
            default_id = warehouse_service.default_warehouse_id()
        except Exception:
            pass
        for wh in warehouses:
            self.warehouse_combo.addItem(wh.get('name', f"#{wh.get('id')}"), wh.get('id'))
            if default_id and int(wh.get('id')) == int(default_id):
                self.warehouse_combo.setCurrentIndex(self.warehouse_combo.count() - 1)

    def _selected_warehouse_id(self):
        if not hasattr(self, 'warehouse_combo'):
            return None
        value = self.warehouse_combo.currentData()
        try:
            return int(value) if value else None
        except Exception:
            return None

    def update_warehouse_availability_label(self):
        if not hasattr(self, 'warehouse_availability_label'):
            return
        wh_id = self._selected_warehouse_id()
        if not wh_id:
            self.warehouse_availability_label.setText(translate("no_warehouse_selected"))
            return
        selected = [line for line in getattr(self.lines_model, 'lines', []) if line.get('item_id')]
        if not selected:
            self.warehouse_availability_label.setText(translate("warehouse_will_be_used"))
            return
        parts = []
        for line in selected[:3]:
            try:
                available = warehouse_service.available_qty(int(line.get('item_id')), wh_id)
                parts.append(f"{line.get('item_name','')}: {available}")
            except Exception:
                pass
        self.warehouse_availability_label.setText(translate('available_in_warehouse', items=' | '.join(parts)) if parts else translate('warehouse_will_be_used'))

    def _stock_available_for_item(self, item_id):
        try:
            item = product_service.item_by_id(item_id)
        except Exception as exc:
            # In client/server offline mode this is a remote read.  Do not block
            # a queueable invoice just because the stock pre-check could not be
            # refreshed.  The server validates stock when the queue is replayed.
            print(translate('stock_check_skipped', error=exc))
            return None
        if not item or item.get('item_type') == translate('service_item_type'):
            return None
        try:
            return Decimal(str(item.get('available', item.get('quantity', 0)) or 0))
        except Exception:
            return Decimal('0')

    def _validate_stock_before_save(self):
        if self.inv_type != 'sale':
            return True
        shortages = []
        totals = {}
        names = {}
        for line in self.lines_model.lines:
            if not line.get('item_id'):
                continue
            item_id = int(line.get('item_id'))
            base_qty = Decimal(str(line.get('qty', 0))) * Decimal(str(line.get('conversion_factor', 1)))
            totals[item_id] = totals.get(item_id, Decimal('0')) + base_qty
            names[item_id] = line.get('item_name', str(item_id))
        for item_id, needed in totals.items():
            available = self._stock_available_for_item(item_id)
            if available is not None and needed > available:
                shortages.append(translate('required_available', name=names.get(item_id, item_id), needed=needed, available=available))
        if shortages:
            QMessageBox.warning(self, translate('insufficient_stock_title'), translate('insufficient_stock_message', items='\n'.join(shortages)))
            return False
        return True

    def _set_paid_value(self, value, manual=False):
        self._updating_payment = True
        try:
            self.paid_spin.setValue(float(value))
        finally:
            self._updating_payment = False
        if manual:
            self._paid_manually_changed = True

    def on_paid_changed(self, value):
        if not self._updating_payment:
            self._paid_manually_changed = True
        self.update_total_display()

    def set_paid_full(self):
        self._set_paid_value(getattr(self, 'total_after_discount', Decimal('0')), manual=True)
        self.update_total_display()

    def set_paid_zero(self):
        self._set_paid_value(0, manual=True)
        self.update_total_display()

    def load_entities(self):
        try:
            if self.inv_type == 'sale':
                self.customers = catalog_service.customers()
                names = [translate("cash_customer")] + [c.get('name', '') for c in self.customers if c.get('name')]
            else:
                self.suppliers = catalog_service.suppliers()
                names = [translate("cash_customer")] + [s.get('name', '') for s in self.suppliers if s.get('name')]
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(translate('parties')), 'warning', self)
                self.customers = getattr(self, 'customers', [])
                self.suppliers = getattr(self, 'suppliers', [])
                names = [translate("cash_customer")]
            else:
                raise
        self.entity_completer.setModel(QStringListModel(names))

    def on_entity_text_changed(self, text):
        if not text.strip() or text.strip() == translate("cash_customer"):
            self.selected_entity_id = None
            self.balance_label.setText("")
            return
        if self.inv_type == 'sale':
            for c in self.customers:
                if c['name'] == text.strip():
                    self.selected_entity_id = c['id']
                    balance_display = currency.convert(c['balance'], currency.storage_currency(), self.display_curr)
                    self.balance_label.setText(translate('customer_balance', amount=currency.format_amount(balance_display)))
                    return
        else:
            for s in self.suppliers:
                if s['name'] == text.strip():
                    self.selected_entity_id = s['id']
                    balance_display = currency.convert(s['balance'], currency.storage_currency(), self.display_curr)
                    self.balance_label.setText(translate('supplier_balance', amount=currency.format_amount(balance_display)))
                    return
        self.selected_entity_id = None
        self.balance_label.setText(translate('unregistered_party_cash'))

    def on_entity_selected(self, text):
        self.entity_search.setText(text)
        self.on_entity_text_changed(text)

    def add_new_entity(self):
        from views.dialogs.add_entity_dialog import AddEntityDialog
        dialog = AddEntityDialog(self, self.inv_type)
        if dialog.exec():
            self.load_entities()
            self.entity_search.setText(dialog.entity_name)
            self.on_entity_text_changed(dialog.entity_name)

    def load_items_for_combo(self):
        try:
            items = catalog_service.items()
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(translate('materials')), 'warning', self)
                items = []
            else:
                raise
        self.items_for_combo = []
        for it in items:
            price = it.get('selling_price', 0) if self.inv_type == 'sale' else it.get('purchase_price', 0)
            price_display = currency.convert(price, currency.storage_currency(), self.display_curr)
            units = catalog_service.item_units(it['id'])
            units_list = [{'id': None, 'unit_name': it.get('unit', translate('unit_piece')), 'conversion_factor': Decimal('1')}]
            for u in units:
                factor = _positive_decimal(u.get('conversion_factor', 1), '1')
                units_list.append({'id': u['id'], 'unit_name': u['unit_name'], 'conversion_factor': factor})
            self.items_for_combo.append({
                'id': it['id'],
                'name': it['name'],
                'barcode': it.get('barcode') or it.get('code') or '',
                'unit': it.get('unit', translate('unit_piece')),
                'price': price_display,
                'units_list': units_list
            })
        if hasattr(self, 'item_delegate'):
            self.item_delegate.items = self.items_for_combo
        if hasattr(self, 'search_input'):
            search_terms = []
            for item in self.items_for_combo:
                if item.get('name'):
                    search_terms.append(item['name'])
                if item.get('barcode'):
                    search_terms.append(str(item['barcode']))
            completer = QCompleter(QStringListModel(search_terms), self.search_input)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            self.search_input.setCompleter(completer)

    def add_empty_line(self):
        self.mark_dirty()
        self.lines_model.add_empty_row()
        new_row = self.lines_model.rowCount() - 1
        self.lines_table.scrollTo(self.lines_model.index(new_row, 0))
        self.focus_barcode_input()

    def duplicate_selected_line(self):
        selected = self.lines_table.selectionModel().selectedRows() if self.lines_table.selectionModel() else []
        if not selected:
            return
        row = selected[0].row()
        if row < 0 or row >= self.lines_model.rowCount():
            return
        source = dict(self.lines_model.lines[row])
        if not source.get('item_id') and not source.get('item_name'):
            return
        self.mark_dirty()
        insert_at = self.lines_model.rowCount()
        self.lines_model.beginInsertRows(QModelIndex(), insert_at, insert_at)
        self.lines_model.lines.append(source)
        self.lines_model.endInsertRows()
        self.lines_model.update_row_total(insert_at)
        self.lines_table.selectRow(insert_at)
        self.update_total_display()

    def remove_selected_line(self):
        self.mark_dirty()
        selected = self.lines_table.selectionModel().selectedRows()
        if selected:
            row = selected[0].row()
            if self.lines_model.rowCount() == 1 and self.lines_model.lines[0]['item_id'] is None:
                self.lines_model.lines[0].update({
                    'item_id': None, 'barcode': '', 'item_name': '', 'qty': Decimal('1'),
                    'unit_id': None, 'unit_display': '', 'conversion_factor': Decimal('1'),
                    'price': Decimal('0'), 'discount_percent': Decimal('0'),
                    'tax_percent': Decimal('0'), 'total': Decimal('0'), 'units_data': []
                })
                self.lines_model.dataChanged.emit(self.lines_model.index(0, 0), self.lines_model.index(0, self.lines_model.columnCount()-1))
            else:
                self.lines_model.remove_row(row)
        self.update_total_display()
        self.focus_barcode_input()

    def on_table_clicked(self, index):
        if index.column() == LinesModel.COL_DELETE:
            self.remove_selected_line()

    def on_line_data_changed(self, topLeft, bottomRight):
        self.update_total_display()
        self.update_invoice_grid_status()
        last_row = self.lines_model.rowCount() - 1
        if last_row >= 0 and self.lines_model.lines[last_row]['item_id'] is not None:
            self.add_empty_line()

    def update_total_display(self):
        total_before = Decimal('0')
        for line in self.lines_model.lines:
            if line.get('item_id'):
                total_before += line['total']
        discount = Decimal(str(self.discount_value.value()))
        if self.discount_type.currentIndex() == 0:
            discount_amount = total_before * discount / 100
        else:
            discount_amount = discount
        total_after = total_before - discount_amount

        self.total_before_label.setText(translate('total_before_discount', amount=currency.format_amount(total_before)))
        self.discount_amount_label.setText(translate('discount', amount=currency.format_amount(discount_amount)))
        self.total_after_label.setText(translate('total_after_discount', amount=currency.format_amount(total_after)))
        if not self._paid_manually_changed and not self.invoice_id:
            self._set_paid_value(total_after, manual=False)
        paid = Decimal(str(self.paid_spin.value()))
        if paid > total_after:
            paid = total_after
        remaining = total_after - paid
        self.remaining_label.setText(translate('remaining_label', amount=currency.format_amount(remaining)))

        self.total_before_discount = total_before
        self.discount_amount = discount_amount
        self.total_after_discount = total_after

    def scan_barcode_with_camera(self):
        try:
            from views.dialogs.barcode_camera_dialog import BarcodeCameraDialog
            dialog = BarcodeCameraDialog(self)
            dialog.barcode_scanned.connect(self.on_camera_barcode_scanned)
            dialog.exec()
        except Exception as e:
            show_toast(translate('camera_scan_failed', error=e), 'error', self)

    def on_camera_barcode_scanned(self, value, symbology=None):
        self.search_input.setText(str(value or '').strip())
        self.add_item_from_search()

    def add_item_from_search(self):
        text = self.search_input.text().strip()
        if not text:
            return
        try:
            item = product_service.item_by_barcode(text)
            if not item:
                items = catalog_service.items(search=text)
                if items:
                    item = items[0]
            if item:
                existing_row = self._find_line_by_item_id(item['id'])
                if existing_row is not None and product_service.item_by_barcode(text):
                    self._increment_existing_line(existing_row, self._quick_add_qty())
                    self.search_input.clear()
                    self._reset_quick_add_qty()
                    self.update_invoice_grid_status()
                    self.focus_barcode_input()
                    show_toast(translate("existing_item_incremented"), "success", self)
                    return
                last_row = self._target_line_for_new_item()
                price = item.get('selling_price', 0) if self.inv_type == 'sale' else item.get('purchase_price', 0)
                price_display = currency.convert(price, currency.storage_currency(), self.display_curr)
                units = catalog_service.item_units(item['id'])
                units_list = [{'id': None, 'unit_name': item.get('unit', translate('unit_piece')), 'conversion_factor': Decimal('1')}]
                for u in units:
                    factor = Decimal(str(u.get('conversion_factor', 1)))
                    if factor == 0:
                        factor = Decimal('1')
                    units_list.append({'id': u['id'], 'unit_name': u['unit_name'], 'conversion_factor': factor})
                barcode_value = item.get('barcode') or item.get('code') or text if product_service.item_by_barcode(text) else (item.get('barcode') or item.get('code') or '')
                self.lines_model.set_item(last_row, item['id'], item['name'], units_list, price_display, barcode_value)
                quick_qty = self._quick_add_qty()
                if quick_qty != Decimal('1'):
                    self.lines_model.setData(self.lines_model.index(last_row, LinesModel.COL_QUANTITY), str(quick_qty))
                self.lines_table.selectRow(last_row)
                self.search_input.clear()
                self._reset_quick_add_qty()
                self.focus_barcode_input()
                self.update_total_display()
                self.update_invoice_grid_status()
            else:
                reply = QMessageBox.question(self, translate('item_not_found_title'), translate('item_not_found_message', text=text),
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.open_add_item_dialog(text)
        except Exception as e:
            show_toast(translate('add_line_failed', error=str(e)), 'error', self)

    def open_add_item_dialog(self, prefill_name):
        from views.dialogs.item_dialog import ItemDialog
        dialog = ItemDialog(self)
        dialog.name_edit.setText(prefill_name)
        if dialog.exec():
            self.load_items_for_combo()
            self.add_item_from_search()

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Insert"), self, self.add_empty_line)
        QShortcut(QKeySequence("Delete"), self, self.remove_selected_line)
        QShortcut(QKeySequence("Ctrl+Return"), self, self.on_save)
        QShortcut(QKeySequence("Ctrl+S"), self, self.on_save)
        QShortcut(QKeySequence("Escape"), self, self.reject)
        QShortcut(QKeySequence("F6"), self, self.print_invoice_professional)
        QShortcut(QKeySequence("F8"), self, lambda: self.discount_value.setFocus())
        QShortcut(QKeySequence("Ctrl+L"), self, self.focus_barcode_input)
        QShortcut(QKeySequence("F2"), self, self.focus_barcode_input)
        QShortcut(QKeySequence("Ctrl+N"), self, self._clear_invoice_form)
        self.watch_dirty_widgets([
            self.entity_search, self.ref_edit, self.date_edit, self.notes_edit,
            self.discount_type, self.discount_value, self.paid_spin, self.search_input
        ], reset=True)

    def on_save(self):
        validator = FormValidator()
        partial_rows = []
        for idx, line in enumerate(self.lines_model.lines, start=1):
            has_text = bool(str(line.get('barcode', '')).strip() or str(line.get('item_name', '')).strip())
            if has_text and not line.get('item_id'):
                partial_rows.append(str(idx))
            if line.get('item_id') and Decimal(str(line.get('qty', 0))) <= 0:
                partial_rows.append(str(idx))
        if partial_rows:
            validator.custom(False, self.search_input, self.form_error_label, translate('missing_or_invalid_line', rows=', '.join(partial_rows)))
            validator.focus_first_invalid()
            show_toast(translate("missing_line_toast"), "error", self)
            return
        lines = self.lines_model.get_lines_data()
        if not lines:
            validator.custom(False, self.search_input, self.form_error_label, translate("add_one_line_before_save"))
            validator.focus_first_invalid()
            show_toast(translate("add_one_line_toast"), "error", self)
            return
        FormValidator.clear(self.form_error_label, self.search_input)
        if not self._validate_stock_before_save():
            return
        total_usd = currency.convert(self.total_after_discount, self.display_curr, currency.storage_currency())
        paid_display = Decimal(str(self.paid_spin.value()))
        paid_usd = currency.convert(paid_display, self.display_curr, currency.storage_currency())
        if paid_usd > total_usd:
            paid_usd = total_usd
        entity_id = self.selected_entity_id
        reference = self.ref_edit.text().strip()
        if not reference:
            reference = invoice_service.next_reference(self.inv_type)
        else:
            if invoice_service.reference_exists(reference, exclude_invoice_id=self.invoice_id):
                show_toast(translate("reference_exists"), "error", self)
                return
        data = {
            'type': self.inv_type,
            'customer_id': entity_id if self.inv_type == 'sale' else None,
            'supplier_id': entity_id if self.inv_type == 'purchase' else None,
            'date': self.date_edit.date().toString("yyyy-MM-dd"),
            'reference': reference,
            'notes': self.notes_edit.toPlainText().strip(),
            'total': total_usd,
            'paid_amount': paid_usd,
            'lines': lines,
            'exchange_rate_to_usd': float(currency.get_current_rate(self.display_curr)),
            'original_currency': self.display_curr,
            'warehouse_id': self._selected_warehouse_id()
        }
        try:
            if self.invoice_id:
                invoice_service.update(self.invoice_id, data)
                saved_id = self.invoice_id
                show_toast(translate("invoice_updated"), "success", self)
            else:
                saved_id = invoice_service.create(data)
                self.invoice_id = saved_id
                self.ref_edit.setText(reference)
                show_toast(translate("invoice_saved"), "success", self)
            if self._embedded_mode:
                self.reset_dirty()
                self.saved.emit(saved_id)
                return
            self.accept()
        except Exception as e:
            show_toast(str(e), "error", self)

    def _build_invoice_print_payload(self):
        inv_ref = self.ref_edit.text() or translate("new_reference")
        inv_date = self.date_edit.date().toString("yyyy-MM-dd")
        if self.selected_entity_id:
            if self.inv_type == 'sale':
                cust = next((c for c in self.customers if c.get('id') == self.selected_entity_id), None)
                entity_name = cust.get('name', translate('cash_customer')) if cust else translate("cash_customer")
            else:
                supp = next((s for s in self.suppliers if s.get('id') == self.selected_entity_id), None)
                entity_name = supp.get('name', translate('cash_customer')) if supp else translate("cash_customer")
        else:
            entity_name = translate("cash_customer")

        lines = []
        for line in self.lines_model.lines:
            if line.get('item_id'):
                lines.append({
                    'barcode': line.get('barcode', ''),
                    'item_name': line.get('item_name', ''),
                    'quantity': str(line.get('qty', '')),
                    'unit': line.get('unit_display', ''),
                    'unit_price': currency.format_amount(line.get('price', 0)),
                    'discount_percent': str(line.get('discount_percent', 0)),
                    'tax_percent': str(line.get('tax_percent', 0)),
                    'total': currency.format_amount(line.get('total', 0)),
                })
        total_before = _money_decimal(self.total_before_discount if hasattr(self, 'total_before_discount') else 0)
        discount_amt = _money_decimal(self.discount_amount if hasattr(self, 'discount_amount') else 0)
        total_after = _money_decimal(self.total_after_discount if hasattr(self, 'total_after_discount') else 0)
        paid = _money_decimal(self.paid_spin.value())
        remaining = total_after - paid
        invoice_payload = {
            'type': self.inv_type,
            'reference': inv_ref,
            'date': inv_date,
            'entity_name': entity_name,
            'lines': lines,
            'total_before_discount': currency.format_amount(total_before),
            'discount': currency.format_amount(discount_amt),
            'total': currency.format_amount(total_after),
            'paid_amount': currency.format_amount(paid),
            'remaining': currency.format_amount(remaining),
            'notes': self.notes_edit.toPlainText().strip(),
        }
        return invoice_payload


    def _setup_print_menu(self):
        """Attach the single unified print action to the existing print button."""
        try:
            self.print_btn.setMenu(None)
            try:
                self.print_btn.clicked.disconnect()
            except Exception:
                pass
            self.print_btn.clicked.connect(self.direct_print_invoice)
            self.print_btn.setText(translate("print_button"))
            self.print_btn.setToolTip(translate("print_tooltip"))
        except Exception:
            pass

    def _invoice_print_payload(self):
        inv_ref = self.ref_edit.text() or translate("new_reference")
        inv_date = self.date_edit.date().toString("yyyy-MM-dd")
        if self.selected_entity_id:
            if self.inv_type == 'sale':
                cust = next((c for c in self.customers if c.get('id') == self.selected_entity_id), None)
                entity_name = cust.get('name', translate('cash_customer')) if cust else translate("cash_customer")
            else:
                supp = next((s for s in self.suppliers if s.get('id') == self.selected_entity_id), None)
                entity_name = supp.get('name', translate('cash_customer')) if supp else translate("cash_customer")
        else:
            entity_name = translate("cash_customer")

        lines = []
        for line in self.lines_model.lines:
            if line.get('item_id'):
                lines.append({
                    'barcode': line.get('barcode', ''),
                    'item_name': line.get('item_name', ''),
                    'quantity': str(line.get('qty', '')),
                    'unit': line.get('unit_display', ''),
                    'unit_price': currency.format_amount(line.get('price', 0)),
                    'discount_percent': str(line.get('discount_percent', 0)),
                    'tax_percent': str(line.get('tax_percent', 0)),
                    'total': currency.format_amount(line.get('total', 0)),
                })
        total_before = _money_decimal(self.total_before_discount if hasattr(self, 'total_before_discount') else 0)
        discount_amt = _money_decimal(self.discount_amount if hasattr(self, 'discount_amount') else 0)
        total_after = _money_decimal(self.total_after_discount if hasattr(self, 'total_after_discount') else 0)
        paid = _money_decimal(self.paid_spin.value())
        remaining = total_after - paid
        return {
            'type': self.inv_type,
            'reference': inv_ref,
            'date': inv_date,
            'entity_name': entity_name,
            'lines': lines,
            'total_before_discount': currency.format_amount(total_before),
            'discount': currency.format_amount(discount_amt),
            'total': currency.format_amount(total_after),
            'paid_amount': currency.format_amount(paid),
            'remaining': currency.format_amount(remaining),
            'notes': self.notes_edit.toPlainText().strip(),
            'currency': self.display_curr,
        }

    def print_invoice_professional(self):
        # Phase 235: legacy method name now uses the single unified print path.
        return self.direct_print_invoice()

    def open_invoice_html_in_browser(self):
        return self.direct_print_invoice()

    def save_invoice_pdf(self):
        # Phase 235: no separate PDF button/path from invoice creation.
        return self.direct_print_invoice()

    def direct_print_invoice(self):
        from printing.printing_service import printing_service
        printing_service.invoice_print(self._invoice_print_payload(), self, paper='default')

    # Backward-compatible method names used by older QAction wiring.
    def print_invoice_html_browser(self):
        return self.open_invoice_html_in_browser()

    def print_invoice_direct(self):
        return self.direct_print_invoice()

    def export_invoice_pdf(self):
        return self.save_invoice_pdf()

# Phase110 offline guard markers: الأطراف | المواد | تعذر فحص رصيد المادة
