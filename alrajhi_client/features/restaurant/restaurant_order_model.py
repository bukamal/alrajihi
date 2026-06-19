# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt

from currency import currency
from i18n import translate
from .restaurant_order_schema import restaurant_order_schema


class RestaurantOrderModel(QAbstractTableModel):
    """Read-only model for the active restaurant session order lines.

    The model intentionally carries unit/barcode fields that were introduced in
    the unified barcode pipeline.  This keeps restaurant POS visually aligned
    with POS and invoices without forcing the restaurant workflow into a full
    TransactionDocumentTab.
    """

    def __init__(self, lines: list[dict[str, Any]] | None = None, display_currency: str | None = None, parent=None):
        super().__init__(parent)
        self.columns = restaurant_order_schema()
        self.lines: list[dict[str, Any]] = list(lines or [])
        self.display_currency = display_currency or currency.get_display_currency()

    def set_lines(self, lines: list[dict[str, Any]] | None) -> None:
        self.beginResetModel()
        self.lines = list(lines or [])
        self.endResetModel()

    def set_display_currency(self, display_currency: str | None) -> None:
        self.display_currency = display_currency or currency.get_display_currency()
        if self.rowCount() and self.columnCount():
            self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1), [Qt.DisplayRole])

    def rowCount(self, parent=QModelIndex()):  # type: ignore[override]
        return 0 if parent.isValid() else len(self.lines)

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
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        if row < 0 or row >= len(self.lines) or col < 0 or col >= len(self.columns):
            return None
        line = self.lines[row]
        key = self.columns[col].key
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self._display_value(row, line, key)
        if role == Qt.TextAlignmentRole:
            if getattr(self.columns[col], 'numeric', False) or key in {'row', 'status', 'barcode_scope'}:
                return Qt.AlignCenter
            return Qt.AlignVCenter | Qt.AlignLeft
        if role == Qt.ToolTipRole:
            return self._tooltip(line)
        if role == Qt.UserRole:
            return line
        return None

    def line_at(self, row: int) -> dict[str, Any] | None:
        try:
            if 0 <= int(row) < len(self.lines):
                return self.lines[int(row)]
        except Exception:
            pass
        return None

    def _decimal(self, value: Any, default: str = "0") -> Decimal:
        try:
            return Decimal(str(value if value not in (None, "") else default))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal(default)

    def _format_decimal(self, value: Any) -> str:
        try:
            value = self._decimal(value)
            return format(value.normalize(), 'f').rstrip('0').rstrip('.') or '0'
        except Exception:
            return str(value or '0')

    def _display_money(self, amount_usd: Any) -> str:
        try:
            amount = currency.convert(self._decimal(amount_usd), currency.storage_currency(), self.display_currency)
            return currency.format_amount(amount)
        except Exception:
            return currency.format_amount(Decimal('0'))

    def _line_total(self, line: dict[str, Any]) -> Decimal:
        total = line.get('total') or line.get('line_total') or line.get('amount')
        if total not in (None, ""):
            return self._decimal(total)
        return self._decimal(line.get('quantity'), '0') * self._decimal(line.get('unit_price'), '0')

    def _base_qty(self, line: dict[str, Any]) -> Decimal:
        base_qty = line.get('base_qty')
        if base_qty not in (None, ""):
            return self._decimal(base_qty)
        return self._decimal(line.get('quantity'), '0') * self._decimal(line.get('conversion_factor'), '1')

    def _status_text(self, status: str) -> str:
        status = str(status or 'new')
        return translate(f'restaurant.line_status.{status}')

    def _barcode_scope_text(self, scope: str) -> str:
        scope = str(scope or '').lower()
        if scope == 'unit':
            return translate('pos_barcode_scope_unit')
        if scope in {'base_unit', 'item'}:
            return translate('pos_barcode_scope_item')
        if scope == 'menu':
            return translate('restaurant.barcode_scope_menu')
        if scope == 'manual':
            return translate('restaurant.barcode_scope_manual')
        return ''

    def _modifiers_text(self, line: dict[str, Any]) -> str:
        modifiers = line.get('modifiers') or line.get('modifier_names') or ''
        if isinstance(modifiers, list):
            parts = []
            for modifier in modifiers:
                if isinstance(modifier, dict):
                    parts.append(str(modifier.get('name') or modifier.get('label') or '').strip())
                else:
                    parts.append(str(modifier).strip())
            return ', '.join([p for p in parts if p])
        return str(modifiers or '')

    def _display_value(self, row: int, line: dict[str, Any], key: str):
        if key == 'row':
            return str(row + 1)
        if key == 'item':
            return line.get('item_name') or line.get('name') or ''
        if key == 'modifiers':
            return self._modifiers_text(line)
        if key == 'unit':
            return line.get('unit') or line.get('unit_name') or ''
        if key == 'qty':
            return self._format_decimal(line.get('quantity') or '0')
        if key == 'base_qty':
            return self._format_decimal(self._base_qty(line))
        if key == 'price':
            return self._display_money(line.get('unit_price') or '0')
        if key == 'total':
            return self._display_money(self._line_total(line))
        if key == 'status':
            return self._status_text(line.get('kitchen_status') or 'new')
        if key == 'barcode_scope':
            return self._barcode_scope_text(line.get('barcode_scope') or '')
        if key == 'notes':
            return line.get('notes') or ''
        return ''

    def _tooltip(self, line: dict[str, Any]) -> str:
        parts = []
        scope = self._barcode_scope_text(line.get('barcode_scope') or '')
        if scope:
            parts.append(scope)
        matched = line.get('matched_barcode') or ''
        if matched:
            parts.append(f"{translate('transaction_column_barcode')}: {matched}")
        base_qty = line.get('base_qty')
        if base_qty not in (None, ''):
            parts.append(f"{translate('pos_column_base_qty')}: {self._format_decimal(base_qty)}")
        return '\n'.join(parts) if parts else None
