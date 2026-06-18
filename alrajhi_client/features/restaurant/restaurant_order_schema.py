# -*- coding: utf-8 -*-
from __future__ import annotations

"""Restaurant order line-grid schema.

Restaurant POS is touch-first, but its open-session order lines should still use
our shared transaction grid vocabulary: schema keys, required columns, presets,
responsive visibility, and unit-barcode columns stay aligned with invoices/POS.
"""

from features.transactions.grids.transaction_column_schema import TransactionColumn


def restaurant_order_schema() -> list[TransactionColumn]:
    return [
        TransactionColumn("row", "#", True, True, True, 46, editable=False),
        TransactionColumn("item", "transaction_column_item", True, True, True, 280, True, editable=False),
        TransactionColumn("modifiers", "restaurant_column_modifiers", False, True, False, 170, editable=False),
        TransactionColumn("unit", "transaction_column_unit", False, True, True, 95, editable=False),
        TransactionColumn("qty", "transaction_column_qty", True, True, True, 95, numeric=True, editable=False),
        TransactionColumn("base_qty", "pos_column_base_qty", False, False, False, 110, numeric=True, editable=False),
        TransactionColumn("price", "transaction_column_price", False, True, True, 120, numeric=True, editable=False),
        TransactionColumn("total", "transaction_column_total", True, True, True, 130, numeric=True, editable=False),
        TransactionColumn("status", "restaurant_column_status", False, True, True, 135, editable=False),
        TransactionColumn("barcode_scope", "pos_column_barcode_scope", False, False, False, 125, editable=False),
        TransactionColumn("notes", "transaction_column_notes", False, True, False, 180, editable=False),
    ]
