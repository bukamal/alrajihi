# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal
from typing import Any

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt

from features.manufacturing.grids.manufacturing_column_schema import ManufacturingColumn


class ProductionLifecycleTableModel(QAbstractTableModel):
    """Read-only lifecycle table model for production reservations, consumptions and outputs."""

    NUMERIC_KEYS = {'reserved_qty', 'consumed_qty', 'remaining_qty', 'qty', 'unit_cost', 'total_cost', 'conversion_factor', 'base_qty'}

    def __init__(self, columns: list[ManufacturingColumn], kind: str, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.kind = kind
        self.lines: list[dict[str, Any]] = []

    def rowCount(self, parent=QModelIndex()):  # type: ignore[override]
        return 0 if parent.isValid() else len(self.lines)

    def columnCount(self, parent=QModelIndex()):  # type: ignore[override]
        return 0 if parent.isValid() else len(self.columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):  # type: ignore[override]
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal and 0 <= section < len(self.columns):
            return self.columns[section].title
        return section + 1

    def data(self, index, role=Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid():
            return None
        column = self.columns[index.column()]
        row = self.lines[index.row()]
        if role in (Qt.DisplayRole, Qt.EditRole):
            if column.key == 'row':
                return index.row() + 1
            value = row.get(column.key, '')
            if role == Qt.DisplayRole and column.key in self.NUMERIC_KEYS and value not in ('', None):
                try:
                    return f"{Decimal(str(value)):.3f}".rstrip('0').rstrip('.')
                except Exception:
                    return value
            return value
        if role == Qt.TextAlignmentRole and column.key in self.NUMERIC_KEYS:
            return Qt.AlignRight | Qt.AlignVCenter
        return None

    def flags(self, index):  # type: ignore[override]
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled if index.isValid() else Qt.NoItemFlags

    def load_rows(self, rows: list[dict[str, Any]] | None) -> None:
        self.beginResetModel()
        normalizer = {
            'reservations': self._normalize_reservation,
            'consumptions': self._normalize_consumption,
            'outputs': self._normalize_output,
        }.get(self.kind, self._normalize_generic)
        self.lines = [normalizer(row or {}) for row in (rows or [])]
        self.endResetModel()

    def get_id(self, row: int):
        if 0 <= row < len(self.lines):
            return self.lines[row].get('id')
        return None

    def get_row(self, row: int) -> dict[str, Any] | None:
        if 0 <= row < len(self.lines):
            return dict(self.lines[row])
        return None

    def summary(self) -> dict[str, Decimal]:
        qty = Decimal('0')
        total = Decimal('0')
        remaining = Decimal('0')
        for row in self.lines:
            qty += self._decimal(row.get('qty') or row.get('reserved_qty'))
            total += self._decimal(row.get('total_cost'))
            remaining += self._decimal(row.get('remaining_qty'))
        return {'line_count': Decimal(str(len(self.lines))), 'qty': qty, 'total_cost': total, 'remaining_qty': remaining}

    def _normalize_reservation(self, row: dict[str, Any]) -> dict[str, Any]:
        reserved = self._decimal(row.get('reserved_qty') or row.get('required_qty') or row.get('qty') or 0)
        consumed = self._decimal(row.get('consumed_qty') or 0)
        remaining = reserved - consumed
        if remaining < 0:
            remaining = Decimal('0')
        return {
            'id': row.get('id') or row.get('reservation_id'),
            'item_id': row.get('item_id'),
            'item': self._item_label(row),
            'unit': row.get('unit_name') or row.get('unit') or row.get('base_unit') or '',
            'reserved_qty': reserved,
            'consumed_qty': consumed,
            'remaining_qty': remaining,
            'conversion_factor': self._decimal(row.get('conversion_factor') or 1),
            'base_qty': reserved,
            'raw': row,
        }

    def _normalize_consumption(self, row: dict[str, Any]) -> dict[str, Any]:
        qty = self._decimal(row.get('consumed_qty') or row.get('qty') or 0)
        cost = self._decimal(row.get('unit_cost') or 0)
        return {
            'id': row.get('id') or row.get('consumption_id'),
            'item_id': row.get('item_id'),
            'item': self._item_label(row),
            'unit': row.get('unit_name') or row.get('unit') or row.get('base_unit') or '',
            'qty': qty,
            'unit_cost': cost,
            'total_cost': qty * cost,
            'date': row.get('movement_date') or row.get('date') or '',
            'raw': row,
        }

    def _normalize_output(self, row: dict[str, Any]) -> dict[str, Any]:
        qty = self._decimal(row.get('produced_qty') or row.get('qty') or 0)
        cost = self._decimal(row.get('unit_cost') or 0)
        return {
            'id': row.get('id') or row.get('output_id'),
            'item_id': row.get('item_id') or row.get('product_id'),
            'item': self._item_label(row),
            'unit': row.get('unit_name') or row.get('unit') or row.get('base_unit') or '',
            'qty': qty,
            'unit_cost': cost,
            'total_cost': qty * cost,
            'date': row.get('output_date') or row.get('date') or '',
            'raw': row,
        }

    def _normalize_generic(self, row: dict[str, Any]) -> dict[str, Any]:
        return dict(row)

    @staticmethod
    def _item_label(row: dict[str, Any]) -> str:
        name = (row.get('item_name') or row.get('product_name') or row.get('name') or row.get('item') or '').strip()
        if name:
            return name
        item_id = row.get('item_id') or row.get('product_id') or row.get('id')
        return f"#{item_id}" if item_id else ''

    @staticmethod
    def _decimal(value) -> Decimal:
        try:
            if value in (None, ''):
                return Decimal('0')
            return Decimal(str(value))
        except Exception:
            return Decimal('0')
