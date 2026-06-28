# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt

from core.money_display_policy import format_money, format_quantity
from core.services.catalog_service import catalog_service
from features.manufacturing.grids.manufacturing_column_schema import ManufacturingColumn
from features.transactions.grids.unified_grid_navigation_policy import is_empty_transaction_line


class BomComponentsModel(QAbstractTableModel):
    """Unit-aware BOM components model.

    The model implements the same editor contract used by TransactionItemDelegate
    and TransactionUnitDelegate: set_item(), set_unit(), and unit_options_for_row().
    This lets BOM component cells resolve materials, unit barcodes and conversion
    factors through the same path used by invoices and POS.
    """

    NUMERIC_KEYS = {'qty', 'base_qty', 'waste_percent', 'unit_cost', 'total_cost'}

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
            if role == Qt.DisplayRole and column.numeric and value not in ('', None):
                try:
                    d = Decimal(str(value))
                    if column.key in {'unit_cost', 'total_cost'}:
                        return format_money(d)
                    if column.key in {'qty', 'base_qty'}:
                        return format_quantity(d, decimals=4)
                    if column.key == 'waste_percent':
                        return f'{format_quantity(d, decimals=2)}%'
                    return format_quantity(d, decimals=4)
                except Exception:
                    return value
            return value
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        return None

    def flags(self, index):  # type: ignore[override]
        if not index.isValid():
            return Qt.NoItemFlags
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if self.columns[index.column()].editable:
            flags |= Qt.ItemIsEditable
        return flags

    def setData(self, index, value, role=Qt.EditRole):  # type: ignore[override]
        if role != Qt.EditRole or not index.isValid():
            return False
        key = self.columns[index.column()].key
        if key == 'row':
            return False
        if key == 'unit':
            if isinstance(value, dict):
                return self.set_unit(index.row(), value)
            self.lines[index.row()][key] = str(value or '')
            self._emit_row_changed(index.row())
            return True
        if key in self.NUMERIC_KEYS:
            value = self._decimal(value)
            if key == 'waste_percent' and value < 0:
                value = Decimal('0')
            if key == 'qty' and value < 0:
                value = Decimal('0')
        self.lines[index.row()][key] = value
        self._recalculate_row(index.row())
        self._emit_row_changed(index.row())
        return True

    def _empty_line(self) -> dict[str, Any]:
        row = {col.key: '' for col in self.columns}
        row.update({
            'item_id': None,
            'unit_id': None,
            'unit_options': [],
            'conversion_factor': Decimal('1'),
            'qty': Decimal('0'),
            'base_qty': Decimal('0'),
            'waste_percent': Decimal('0'),
            'unit_cost': Decimal('0'),
            'base_unit_cost': Decimal('0'),
            'total_cost': Decimal('0'),
        })
        return row

    def is_empty_line(self, row_index: int) -> bool:
        """Return True when a row is the reusable blank BOM component line."""
        if not (0 <= row_index < len(self.lines)):
            return False
        return is_empty_transaction_line(self.lines[row_index])

    def trim_extra_trailing_empty_lines(self) -> int:
        """Keep one reusable blank tail row and remove duplicate blank tails."""
        removed = 0
        while len(self.lines) > 1 and self.is_empty_line(len(self.lines) - 1) and self.is_empty_line(len(self.lines) - 2):
            row_index = len(self.lines) - 1
            self.beginRemoveRows(QModelIndex(), row_index, row_index)
            self.lines.pop()
            self.endRemoveRows()
            removed += 1
        return removed

    def ensure_single_trailing_empty_line(self) -> int:
        """Idempotent BOM append gate used by Enter and Insert."""
        self.trim_extra_trailing_empty_lines()
        if self.lines and self.is_empty_line(len(self.lines) - 1):
            return len(self.lines) - 1
        row_index = len(self.lines)
        self.beginInsertRows(QModelIndex(), row_index, row_index)
        self.lines.append(self._empty_line())
        self.endInsertRows()
        self.trim_extra_trailing_empty_lines()
        return min(row_index, len(self.lines) - 1)

    def add_empty_line(self) -> int:
        """Compatibility API; Phase418 makes it idempotent by design."""
        return self.ensure_single_trailing_empty_line()

    def clear(self, keep_empty: bool = True) -> None:
        self.beginResetModel()
        self.lines = []
        self.endResetModel()
        if keep_empty:
            self.add_empty_line()

    def remove_row(self, row_index: int) -> bool:
        if not (0 <= row_index < len(self.lines)):
            return False
        self.beginRemoveRows(QModelIndex(), row_index, row_index)
        self.lines.pop(row_index)
        self.endRemoveRows()
        if not self.lines:
            self.ensure_single_trailing_empty_line()
        return True

    def add_item(self, item: dict[str, Any], qty=1, price_key: str = 'purchase_price') -> int:
        if not self.lines or not self.is_empty_line(len(self.lines) - 1):
            self.ensure_single_trailing_empty_line()
        row_index = len(self.lines) - 1
        self.set_item(row_index, item, price_key=price_key, qty=qty)
        return row_index

    def set_item(self, row_index: int, item: dict[str, Any], price_key: str = 'purchase_price', qty=None, warehouse_available=None) -> bool:
        if not item or not (0 <= row_index < len(self.lines)):
            return False
        matched_unit = item.get('matched_unit') or {}
        factor = self._positive_decimal(
            matched_unit.get('conversion_factor')
            or item.get('conversion_factor')
            or item.get('factor')
            or 1
        )
        base_cost = self._decimal(
            item.get('base_unit_cost')
            or item.get('average_cost')
            or item.get(price_key)
            or item.get('purchase_price')
            or item.get('unit_cost')
            or 0
        )
        unit_cost = self._money(base_cost * factor)
        unit = matched_unit.get('unit_name') or matched_unit.get('unit') or item.get('unit') or item.get('unit_name') or ''
        unit_id = matched_unit.get('unit_id') if matched_unit else item.get('unit_id')
        barcode = item.get('matched_barcode') or matched_unit.get('barcode') or item.get('barcode') or item.get('code') or ''
        current_qty = self._decimal(self.lines[row_index].get('qty'))
        qty_value = self._decimal(qty) if qty is not None else (current_qty if current_qty > 0 else Decimal('1'))
        self.lines[row_index].update({
            'item_id': item.get('id'),
            'barcode': barcode,
            'item': item.get('name') or item.get('item_name') or '',
            'unit': unit,
            'unit_id': unit_id,
            'conversion_factor': factor,
            'unit_options': self._unit_options_for_item(item, unit, unit_id, factor),
            'base_unit_cost': base_cost,
            'unit_cost': unit_cost,
            'qty': qty_value,
        })
        self._recalculate_row(row_index)
        self._emit_row_changed(row_index)
        return True

    def set_unit(self, row_index: int, unit_data: dict[str, Any]) -> bool:
        if not (0 <= row_index < len(self.lines)):
            return False
        row = self.lines[row_index]
        factor = self._positive_decimal(unit_data.get('conversion_factor') or 1)
        row.update({
            'unit': unit_data.get('unit_name') or unit_data.get('unit') or '',
            'unit_id': unit_data.get('unit_id') or unit_data.get('id'),
            'conversion_factor': factor,
        })
        base_cost = self._decimal(row.get('base_unit_cost') or 0)
        row['unit_cost'] = self._money(base_cost * factor)
        self._recalculate_row(row_index)
        self._emit_row_changed(row_index)
        return True

    def unit_options_for_row(self, row_index: int) -> list[dict[str, Any]]:
        if not (0 <= row_index < len(self.lines)):
            return []
        row = self.lines[row_index]
        return row.get('unit_options') or self._unit_options_for_line(row)

    def load_lines(self, lines: list[dict[str, Any]] | None) -> None:
        self.beginResetModel()
        self.lines = []
        for line in lines or []:
            row = self._empty_line()
            factor = self._positive_decimal(line.get('conversion_factor') or 1)
            qty = self._decimal(line.get('quantity') or line.get('qty') or 0)
            waste = self._decimal(line.get('waste_percent') or 0)
            if waste > 1:
                waste = waste / Decimal('100')
            unit_cost = self._decimal(line.get('unit_cost') or line.get('cost') or line.get('purchase_price') or 0)
            row.update({
                'item_id': line.get('item_id'),
                'barcode': line.get('barcode') or line.get('item_barcode') or '',
                'item': line.get('item_name') or line.get('name') or '',
                'unit': line.get('unit') or line.get('unit_name') or '',
                'unit_id': line.get('unit_id'),
                'conversion_factor': factor,
                'unit_options': self._unit_options_for_line(line, line.get('unit') or line.get('unit_name') or '', line.get('unit_id'), factor),
                'qty': qty,
                'waste_percent': waste * Decimal('100'),
                'base_unit_cost': unit_cost / factor if factor else unit_cost,
                'unit_cost': unit_cost,
                'notes': line.get('notes') or '',
            })
            self._recalculate_row_data(row)
            self.lines.append(row)
        self.endResetModel()
        if not self.lines:
            self.ensure_single_trailing_empty_line()

    def payload_lines(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for row in self.lines:
            if not row.get('item_id'):
                continue
            waste_percent = self._decimal(row.get('waste_percent')) / Decimal('100')
            result.append({
                'item_id': row.get('item_id'),
                'quantity': str(self._decimal(row.get('qty'))),
                'unit_id': row.get('unit_id'),
                'waste_percent': str(waste_percent),
                'conversion_factor': str(self._positive_decimal(row.get('conversion_factor') or 1)),
                'base_qty': str(self._decimal(row.get('base_qty'))),
                'unit_cost': str(self._decimal(row.get('unit_cost'))),
                'notes': row.get('notes') or '',
            })
        return result

    def validation_errors(self, product_id=None) -> list[str]:
        errors: list[str] = []
        seen = set()
        for row_number, row in enumerate(self.lines, start=1):
            if not row.get('item_id'):
                continue
            if product_id and row.get('item_id') == product_id:
                errors.append(f'BOM row {row_number}: self component')
            qty = self._decimal(row.get('qty'))
            if qty <= 0:
                errors.append(f'BOM row {row_number}: quantity must be positive')
            unit_id = row.get('unit_id') or None
            key = (row.get('item_id'), unit_id)
            if key in seen:
                errors.append(f'BOM row {row_number}: duplicate component')
            seen.add(key)
        if not any(row.get('item_id') for row in self.lines):
            errors.append('BOM has no components')
        return errors

    def cost_summary(self) -> dict[str, Decimal]:
        material_cost = Decimal('0')
        base_qty = Decimal('0')
        waste_cost = Decimal('0')
        for row in self.lines:
            if not row.get('item_id'):
                continue
            material_cost += self._decimal(row.get('total_cost'))
            qty = self._decimal(row.get('qty'))
            factor = self._positive_decimal(row.get('conversion_factor') or 1)
            waste_multiplier = Decimal('1') + (self._decimal(row.get('waste_percent')) / Decimal('100'))
            base_qty += qty * factor * waste_multiplier
            waste_cost += qty * self._decimal(row.get('unit_cost')) * (waste_multiplier - Decimal('1'))
        return {
            'material_cost': material_cost,
            'waste_cost': waste_cost,
            'base_qty': base_qty,
            'line_count': Decimal(str(sum(1 for row in self.lines if row.get('item_id')))),
        }

    def _recalculate_row(self, row_index: int) -> None:
        if 0 <= row_index < len(self.lines):
            self._recalculate_row_data(self.lines[row_index])

    def _recalculate_row_data(self, row: dict[str, Any]) -> None:
        qty = self._decimal(row.get('qty'))
        factor = self._positive_decimal(row.get('conversion_factor') or 1)
        waste_multiplier = Decimal('1') + (self._decimal(row.get('waste_percent')) / Decimal('100'))
        unit_cost = self._decimal(row.get('unit_cost'))
        row['base_qty'] = self._qty(qty * factor * waste_multiplier)
        row['total_cost'] = self._money(qty * unit_cost * waste_multiplier)

    def _unit_options_for_item(self, item: dict[str, Any], unit: str = '', unit_id=None, factor=Decimal('1')) -> list[dict[str, Any]]:
        options = self._unit_options_for_line(item, unit, unit_id, factor)
        try:
            for unit_row in catalog_service.item_units(int(item.get('id'))):
                row = dict(unit_row or {})
                row.setdefault('unit_id', row.get('id'))
                row.setdefault('unit_name', row.get('unit') or row.get('name') or '')
                row.setdefault('conversion_factor', row.get('factor') or row.get('conversion') or '1')
                if row.get('unit_name') and not any(str(row.get('unit_id')) == str(existing.get('unit_id')) for existing in options):
                    options.append(row)
        except Exception:
            pass
        return options

    def _unit_options_for_line(self, line: dict[str, Any], unit: str = '', unit_id=None, factor=Decimal('1')) -> list[dict[str, Any]]:
        options: list[dict[str, Any]] = []
        if unit:
            options.append({'unit_id': unit_id, 'unit_name': unit, 'conversion_factor': str(factor)})
        else:
            options.append({'unit_id': None, 'unit_name': '', 'conversion_factor': '1'})
        return options

    def _emit_row_changed(self, row_index: int) -> None:
        if 0 <= row_index < len(self.lines):
            self.dataChanged.emit(self.index(row_index, 0), self.index(row_index, len(self.columns) - 1), [Qt.DisplayRole, Qt.EditRole])
            try:
                self.layoutChanged.emit()
            except Exception:
                pass

    def _decimal(self, value, default='0') -> Decimal:
        try:
            if value in (None, ''):
                value = default
            return Decimal(str(value))
        except Exception:
            return Decimal(str(default))

    def _positive_decimal(self, value) -> Decimal:
        value = self._decimal(value, '1')
        return value if value > 0 else Decimal('1')

    def _qty(self, value) -> Decimal:
        return Decimal(value).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

    def _money(self, value) -> Decimal:
        return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
