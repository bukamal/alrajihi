# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal
from PyQt5.QtCore import Qt

from views.widgets.returns_widget import (
    RET_COL_RETURN_QTY,
    RET_COL_NOTES,
    _ret_dec,
    _ret_returnable_base,
    _ret_unit_price_usd_for_factor,
)


class ReturnLinesComponent:
    """Unit-aware return lines boundary.

    The component keeps return quantity/unit payload extraction outside the tab
    shell, so sales returns, purchase returns and future exchange flows can use
    the same rules.
    """

    def __init__(self, host, qty_kind: str) -> None:
        self.host = host
        self.qty_kind = qty_kind

    def rows(self) -> list[dict]:
        return list(getattr(self.host, 'line_rows', []) or [])

    def payload(self) -> list[dict]:
        lines = []
        table = self.host.lines_table
        for row, line in enumerate(self.rows()):
            try:
                qty_item = table.item(row, RET_COL_RETURN_QTY)
                qty = _ret_dec(qty_item.text() if qty_item else 0)
            except Exception:
                qty = Decimal('0')
            if qty <= 0:
                continue
            factor = _ret_dec(line.get('_selected_factor') or line.get('conversion_factor') or 1, '1')
            if factor <= 0:
                factor = Decimal('1')
            base_qty = qty * factor
            notes_item = table.item(row, RET_COL_NOTES)
            lines.append({
                'original_invoice_line_id': line.get('id'),
                'quantity': str(qty),
                'quantity_in_base': str(base_qty),
                'conversion_factor': str(factor),
                'unit': line.get('_selected_unit') or line.get('unit') or '',
                'unit_id': line.get('_selected_unit_id'),
                'unit_price': str(_ret_unit_price_usd_for_factor(line, factor)),
                'notes': notes_item.text() if notes_item else '',
            })
        return lines

    def validate(self) -> tuple[bool, str]:
        for row, line in enumerate(self.rows()):
            qty_item = self.host.lines_table.item(row, RET_COL_RETURN_QTY)
            qty = _ret_dec(qty_item.text() if qty_item else 0)
            factor = _ret_dec(line.get('_selected_factor') or line.get('conversion_factor') or 1, '1')
            if factor <= 0:
                factor = Decimal('1')
            if qty * factor > _ret_returnable_base(line):
                return False, 'return_quantity_exceeds_available'
        return True, ''

    def has_unit_support(self) -> bool:
        return hasattr(self.host, 'lines_table') and self.host.lines_table.columnCount() >= 10
