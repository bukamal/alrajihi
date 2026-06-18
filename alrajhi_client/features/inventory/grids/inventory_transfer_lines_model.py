# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt

from features.inventory.grids.inventory_transfer_schema import inventory_transfer_lines_schema
from features.transactions.i18n import tr


class InventoryTransferLinesModel(QAbstractTableModel):
    """Unit-aware warehouse transfer line model."""

    def __init__(self, columns=None, parent=None):
        super().__init__(parent)
        self.columns = columns or inventory_transfer_lines_schema()
        self.lines: list[dict[str, Any]] = []

    def _decimal(self, value, default='0') -> Decimal:
        try:
            return Decimal(str(value if value not in (None, '') else default))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal(str(default))

    def _positive_decimal(self, value, default='1') -> Decimal:
        value = self._decimal(value, default)
        return value if value > 0 else Decimal(str(default))

    def _empty_line(self) -> dict[str, Any]:
        return {
            'item_id': None, 'barcode': '', 'item': '', 'unit': '', 'unit_id': None,
            'unit_options': [], 'conversion_factor': Decimal('1'), 'qty': Decimal('1'),
            'base_qty': Decimal('1'), 'available': '', 'unit_cost': Decimal('0'),
            'barcode_scope': '', 'matched_barcode': '', 'notes': '',
        }

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
            return section + 1
        return None

    def flags(self, index):  # type: ignore[override]
        if not index.isValid():
            return Qt.NoItemFlags
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if getattr(self.columns[index.column()], 'editable', True):
            flags |= Qt.ItemIsEditable
        return flags

    def data(self, index, role=Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid() or not (0 <= index.row() < len(self.lines)):
            return None
        row = self.lines[index.row()]
        key = self.columns[index.column()].key
        if key == 'row':
            return index.row() + 1 if role in (Qt.DisplayRole, Qt.EditRole) else None
        value = row.get(key, '')
        if role in (Qt.DisplayRole, Qt.EditRole):
            if isinstance(value, Decimal):
                return format(value.normalize(), 'f') if value == value.to_integral() else format(value, 'f')
            return '' if value is None else value
        if role == Qt.TextAlignmentRole and getattr(self.columns[index.column()], 'numeric', False):
            return Qt.AlignVCenter | Qt.AlignRight
        return None

    def setData(self, index, value, role=Qt.EditRole):  # type: ignore[override]
        if role != Qt.EditRole or not index.isValid() or not (0 <= index.row() < len(self.lines)):
            return False
        key = self.columns[index.column()].key
        if key == 'row':
            return False
        row = self.lines[index.row()]
        if key == 'qty':
            row['qty'] = self._decimal(value)
            self._recalculate_row(index.row())
        elif key == 'item':
            row['item'] = str(value or '').strip()
        elif key == 'notes':
            row['notes'] = str(value or '')
        else:
            row[key] = value
            if key == 'conversion_factor':
                self._recalculate_row(index.row())
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True

    def add_empty_line(self) -> None:
        pos = len(self.lines)
        self.beginInsertRows(QModelIndex(), pos, pos)
        self.lines.append(self._empty_line())
        self.endInsertRows()

    def remove_row(self, row: int) -> None:
        if not (0 <= row < len(self.lines)):
            return
        self.beginRemoveRows(QModelIndex(), row, row)
        self.lines.pop(row)
        self.endRemoveRows()
        if not self.lines:
            self.add_empty_line()

    def _emit_row_changed(self, row: int) -> None:
        if not (0 <= row < len(self.lines)):
            return
        self.dataChanged.emit(self.index(row, 0), self.index(row, len(self.columns) - 1), [Qt.DisplayRole, Qt.EditRole])

    def _recalculate_row(self, row: int) -> None:
        if not (0 <= row < len(self.lines)):
            return
        line = self.lines[row]
        factor = self._positive_decimal(line.get('conversion_factor') or 1)
        line['base_qty'] = self._decimal(line.get('qty')) * factor

    def _unit_options_for_item(self, item: dict[str, Any], unit='', unit_id=None, factor=Decimal('1')) -> list[dict[str, Any]]:
        options: list[dict[str, Any]] = []
        seen: set[str] = set()
        for unit_row in item.get('units') or item.get('unit_options') or []:
            if not isinstance(unit_row, dict):
                continue
            name = str(unit_row.get('unit_name') or unit_row.get('unit') or '').strip()
            conv = unit_row.get('conversion_factor') or unit_row.get('factor') or 1
            key = f"{unit_row.get('unit_id') or unit_row.get('id') or ''}:{name}:{conv}"
            if name and key not in seen:
                seen.add(key)
                options.append({'unit_id': unit_row.get('unit_id') or unit_row.get('id'), 'unit_name': name, 'conversion_factor': conv, 'barcode': unit_row.get('barcode') or ''})
        if unit:
            key = f"{unit_id or ''}:{unit}:{factor}"
            if key not in seen:
                options.insert(0, {'unit_id': unit_id, 'unit_name': unit, 'conversion_factor': str(factor)})
        return options

    def unit_options_for_row(self, row: int) -> list[dict[str, Any]]:
        return self.lines[row].get('unit_options') or [] if 0 <= row < len(self.lines) else []

    def set_unit(self, row: int, unit_data: dict[str, Any]) -> bool:
        if not (0 <= row < len(self.lines)):
            return False
        factor = self._positive_decimal(unit_data.get('conversion_factor') or unit_data.get('factor') or 1)
        self.lines[row]['unit_id'] = unit_data.get('unit_id') or unit_data.get('id')
        self.lines[row]['unit'] = unit_data.get('unit_name') or unit_data.get('unit') or ''
        self.lines[row]['conversion_factor'] = factor
        self._recalculate_row(row)
        self._emit_row_changed(row)
        return True

    def set_item(self, row_index: int, item: dict[str, Any], price_key: str = 'purchase_price', qty=None, warehouse_available=None) -> bool:
        if not item or not (0 <= row_index < len(self.lines)):
            return False
        matched_unit = item.get('matched_unit') or {}
        factor = self._positive_decimal(matched_unit.get('conversion_factor') or item.get('conversion_factor') or item.get('factor') or 1)
        unit = matched_unit.get('unit_name') or matched_unit.get('unit') or item.get('unit') or item.get('unit_name') or ''
        unit_id = matched_unit.get('unit_id') if matched_unit else item.get('unit_id')
        qty_value = self._decimal(qty) if qty is not None else self._decimal(self.lines[row_index].get('qty') or 1)
        base_cost = self._decimal(item.get('average_cost') or item.get('purchase_price') or item.get('cost') or 0)
        scanned_barcode = item.get('matched_barcode') or matched_unit.get('barcode') or item.get('barcode') or item.get('code') or ''
        self.lines[row_index].update({
            'item_id': item.get('id'), 'barcode': scanned_barcode,
            'item': item.get('name') or item.get('item_name') or '',
            'unit': unit, 'unit_id': unit_id,
            'unit_options': self._unit_options_for_item(item, unit, unit_id, factor),
            'conversion_factor': factor, 'qty': qty_value, 'base_qty': qty_value * factor,
            'available': warehouse_available if warehouse_available not in (None, '') else item.get('available', ''),
            'unit_cost': base_cost,
            'barcode_scope': item.get('barcode_scope') or ('unit' if matched_unit else 'item'),
            'matched_barcode': scanned_barcode,
        })
        self._emit_row_changed(row_index)
        return True

    def apply_availability(self, availability_provider) -> None:
        changed = False
        for line in self.lines:
            item_id = line.get('item_id')
            if item_id:
                try:
                    line['available'] = availability_provider(item_id)
                    changed = True
                except Exception:
                    pass
        if changed and self.lines:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self.lines)-1, len(self.columns)-1), [Qt.DisplayRole])

    def validation_errors(self) -> list[str]:
        errors: list[str] = []
        for row_no, line in enumerate(self.lines, start=1):
            if not any(line.get(k) for k in ('item_id', 'item', 'barcode')):
                continue
            if not line.get('item_id'):
                errors.append(tr('inventory_transfer_line_missing_item', row=row_no)); continue
            qty = self._decimal(line.get('qty'))
            if qty <= 0:
                errors.append(tr('inventory_transfer_line_invalid_qty', row=row_no))
            base_qty = qty * self._positive_decimal(line.get('conversion_factor') or 1)
            available = line.get('available')
            if available not in (None, '') and self._decimal(available) < base_qty:
                errors.append(tr('inventory_transfer_line_shortage', row=row_no))
        return errors

    def payload_lines(self) -> list[dict[str, Any]]:
        payload = []
        for line in self.lines:
            if not line.get('item_id'):
                continue
            qty = self._decimal(line.get('qty'))
            factor = self._positive_decimal(line.get('conversion_factor') or 1)
            base_qty = qty * factor
            if qty <= 0:
                continue
            payload.append({
                'item_id': line.get('item_id'), 'quantity': str(qty), 'base_qty': str(base_qty),
                'unit_id': line.get('unit_id'), 'unit_name': line.get('unit') or '',
                'conversion_factor': str(factor), 'barcode_scope': line.get('barcode_scope') or '',
                'matched_barcode': line.get('matched_barcode') or line.get('barcode') or '',
                'notes': line.get('notes') or '',
            })
        return payload

    def add_item_from_lookup(self, item: dict[str, Any], warehouse_available=None) -> int:
        if not self.lines or self.lines[-1].get('item_id'):
            self.add_empty_line()
        row = len(self.lines) - 1
        self.set_item(row, item, warehouse_available=warehouse_available)
        return row
