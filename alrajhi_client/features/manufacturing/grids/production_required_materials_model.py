# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal
from typing import Any

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt

from core.money_display_policy import format_quantity
from features.manufacturing.grids.manufacturing_column_schema import ManufacturingColumn
from features.manufacturing.i18n import tr


class ProductionRequiredMaterialsModel(QAbstractTableModel):
    """Read-only required-materials model for production orders.

    Quantities are shown in base units returned by the manufacturing service/API.
    The model is deliberately read-only: production-order creation derives
    requirements from the BOM, not from ad-hoc editable invoice lines.
    """

    NUMERIC_KEYS = {'required_qty', 'available_qty', 'shortage_qty', 'conversion_factor', 'base_qty'}

    def __init__(self, columns: list[ManufacturingColumn], parent=None):
        super().__init__(parent)
        self.columns = columns
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
                    return format_quantity(value, decimals=4)
                except Exception:
                    return value
            return value
        if role == Qt.TextAlignmentRole and column.key in self.NUMERIC_KEYS:
            return Qt.AlignRight | Qt.AlignVCenter
        if role == Qt.ForegroundRole and column.key == 'status':
            try:
                from PyQt5.QtGui import QColor
                return QColor('#0b7a3b') if row.get('is_sufficient') else QColor('#b00020')
            except Exception:
                return None
        return None

    def flags(self, index):  # type: ignore[override]
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled if index.isValid() else Qt.NoItemFlags

    def load_materials(self, materials: list[dict[str, Any]] | None) -> None:
        self.beginResetModel()
        self.lines = [self._normalize(row or {}) for row in (materials or [])]
        self.endResetModel()

    def _normalize(self, row: dict[str, Any]) -> dict[str, Any]:
        required = self._decimal(row.get('required_qty') or row.get('quantity') or row.get('base_qty') or 0)
        available = self._decimal(row.get('available_qty') or 0)
        shortage = required - available
        if shortage < 0:
            shortage = Decimal('0')
        sufficient = bool(row.get('is_sufficient')) if 'is_sufficient' in row else available >= required
        unit = row.get('unit_name') or row.get('unit') or row.get('base_unit') or ''
        return {
            'item_id': row.get('item_id'),
            'item': row.get('item_name') or row.get('name') or row.get('item') or '',
            'unit': unit,
            'required_qty': required,
            'available_qty': available,
            'shortage_qty': shortage,
            'status': tr('sufficient') if sufficient else tr('insufficient'),
            'is_sufficient': sufficient,
            'conversion_factor': self._decimal(row.get('conversion_factor') or 1),
            'base_qty': required,
            'raw': row,
        }

    def insufficient_lines(self) -> list[dict[str, Any]]:
        return [row for row in self.lines if not row.get('is_sufficient')]

    def summary(self) -> dict[str, Decimal]:
        required = Decimal('0')
        available = Decimal('0')
        shortage = Decimal('0')
        for row in self.lines:
            required += self._decimal(row.get('required_qty'))
            available += self._decimal(row.get('available_qty'))
            shortage += self._decimal(row.get('shortage_qty'))
        return {
            'line_count': Decimal(str(len(self.lines))),
            'required_qty': required,
            'available_qty': available,
            'shortage_qty': shortage,
            'insufficient_count': Decimal(str(len(self.insufficient_lines()))),
        }

    @staticmethod
    def _decimal(value) -> Decimal:
        try:
            if value in (None, ''):
                return Decimal('0')
            return Decimal(str(value))
        except Exception:
            return Decimal('0')
