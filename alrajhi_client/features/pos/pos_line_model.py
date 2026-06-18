# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt

from currency import currency
from i18n import translate
from core.services.pos_service import POSCart, POSLine
from .pos_line_schema import pos_line_schema


class POSLineModel(QAbstractTableModel):
    """Read-only POS cart model driven by the shared transaction column schema."""

    def __init__(self, cart: POSCart | None = None, display_currency: str | None = None, parent=None):
        super().__init__(parent)
        self.columns = pos_line_schema()
        self.cart = cart
        self.display_currency = display_currency or currency.get_display_currency()

    def set_cart(self, cart: POSCart | None) -> None:
        self.beginResetModel()
        self.cart = cart
        self.endResetModel()

    def set_display_currency(self, display_currency: str | None) -> None:
        self.display_currency = display_currency or currency.get_display_currency()
        if self.rowCount() and self.columnCount():
            top_left = self.index(0, 0)
            bottom_right = self.index(self.rowCount() - 1, self.columnCount() - 1)
            self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])

    def rowCount(self, parent=QModelIndex()):  # type: ignore[override]
        if parent.isValid() or self.cart is None:
            return 0
        return len(self.cart.lines)

    def columnCount(self, parent=QModelIndex()):  # type: ignore[override]
        return 0 if parent.isValid() else len(self.columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):  # type: ignore[override]
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal and 0 <= section < len(self.columns):
            return self.columns[section].title
        if orientation == Qt.Vertical:
            return str(section + 1)
        return None

    def flags(self, index):  # type: ignore[override]
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index, role=Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid() or self.cart is None:
            return None
        row = index.row()
        col = index.column()
        if row < 0 or row >= len(self.cart.lines) or col < 0 or col >= len(self.columns):
            return None
        line = self.cart.lines[row]
        key = self.columns[col].key
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self._display_value(row, line, key)
        if role == Qt.TextAlignmentRole:
            if getattr(self.columns[col], 'numeric', False) or key in {'row', 'barcode_scope'}:
                return Qt.AlignCenter
            return Qt.AlignVCenter | Qt.AlignLeft
        if role == Qt.ToolTipRole:
            try:
                if line.available_qty > 0 and (line.base_qty or line.qty * line.conversion_factor) > (line.available_qty * line.conversion_factor):
                    return translate('sold_qty_exceeds_available_warning')
            except Exception:
                return None
        return None

    def line_at(self, row: int) -> POSLine | None:
        try:
            if self.cart and 0 <= int(row) < len(self.cart.lines):
                return self.cart.lines[int(row)]
        except Exception:
            pass
        return None

    def _format_decimal(self, value) -> str:
        try:
            value = Decimal(str(value))
            return format(value.normalize(), 'f').rstrip('0').rstrip('.') or '0'
        except Exception:
            return str(value or '0')

    def _display_money(self, amount_usd) -> str:
        try:
            amount = currency.convert(Decimal(str(amount_usd or 0)), 'USD', self.display_currency)
            return currency.format_amount(amount)
        except Exception:
            return currency.format_amount(Decimal('0'))

    def _display_value(self, row: int, line: POSLine, key: str):
        if key == 'row':
            return str(row + 1)
        if key == 'barcode':
            return line.barcode or ''
        if key == 'item':
            return line.name or ''
        if key == 'unit':
            return line.unit or ''
        if key == 'qty':
            return self._format_decimal(line.qty)
        if key == 'base_qty':
            return self._format_decimal(line.base_qty or (line.qty * line.conversion_factor))
        if key == 'price':
            return self._display_money(line.unit_price_usd)
        if key == 'total':
            return self._display_money(line.total_usd)
        if key == 'available':
            return self._format_decimal(line.available_qty)
        if key == 'barcode_scope':
            return translate('pos_barcode_scope_unit') if str(line.barcode_scope) == 'unit' else translate('pos_barcode_scope_item')
        return ''
