# -*- coding: utf-8 -*-
"""Inventory ledger shadow-posting policy.

Phase 23 keeps this deliberately small: it derives ledger direction from the
signed quantity and a few known movement-type names, then stores positive
quantities in the append-only inventory_ledger table. It does not replace the
legacy stock balance tables yet.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Tuple

_IN_TYPES = {
    'purchase', 'purchase_in', 'invoice_purchase_in', 'sales_return_in',
    'transfer_in', 'transfer_cancel_in', 'production_out', 'consumption_reverse',
}
_OUT_TYPES = {
    'sale', 'sales_out', 'invoice_sale_out', 'purchase_return_out',
    'transfer_out', 'transfer_cancel_out', 'production_consume',
}


def normalize_ledger_quantity(movement_type: str | None, quantity) -> Tuple[str, Decimal]:
    """Return (direction, positive_quantity) for a legacy movement."""
    qty = Decimal(str(quantity or '0'))
    mt = str(movement_type or '').strip()
    if mt.startswith('reverse_'):
        # Reversal rows are already signed by the caller.
        direction = 'in' if qty > 0 else 'out' if qty < 0 else 'neutral'
    elif mt in _IN_TYPES:
        direction = 'in'
    elif mt in _OUT_TYPES:
        direction = 'out'
    else:
        direction = 'in' if qty > 0 else 'out' if qty < 0 else 'neutral'
    return direction, abs(qty)
