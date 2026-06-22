# -*- coding: utf-8 -*-
from __future__ import annotations

"""Restaurant/cafe order line-grid schemas.

Restaurant and cafe remain backed by the same service engine, but their visible,
printable and exportable columns are now declared by the central universal
column registry.  The functions return the legacy TransactionColumn objects used
by TransactionLineGrid so existing models and delegates stay stable.
"""

from features.transactions.grids.transaction_column_schema import TransactionColumn
from features.transactions.grids.universal_column_adapter import transaction_columns_from_contract


def _fallback_restaurant_order_schema() -> list[TransactionColumn]:
    return [
        TransactionColumn("row", "#", True, True, True, 46, editable=False),
        TransactionColumn("item", "transaction_column_item", True, True, True, 280, True, editable=False),
        TransactionColumn("modifiers", "restaurant_column_modifiers", False, False, False, 170, editable=False),
        TransactionColumn("unit", "transaction_column_unit", False, False, True, 95, editable=False),
        TransactionColumn("qty", "transaction_column_qty", True, True, True, 95, numeric=True, editable=False),
        TransactionColumn("base_qty", "pos_column_base_qty", False, False, False, 110, numeric=True, editable=False),
        TransactionColumn("price", "transaction_column_price", False, True, True, 120, numeric=True, editable=False),
        TransactionColumn("total", "transaction_column_total", True, True, True, 130, numeric=True, editable=False),
        TransactionColumn("status", "restaurant_column_status", False, False, True, 135, editable=False),
        TransactionColumn("barcode_scope", "pos_column_barcode_scope", False, False, False, 125, editable=False),
        TransactionColumn("notes", "transaction_column_notes", False, False, False, 180, editable=False),
    ]


def restaurant_order_schema() -> list[TransactionColumn]:
    return transaction_columns_from_contract("restaurant", "order_lines", _fallback_restaurant_order_schema())


def cafe_order_schema() -> list[TransactionColumn]:
    return transaction_columns_from_contract("cafe", "order_lines", _fallback_restaurant_order_schema())
