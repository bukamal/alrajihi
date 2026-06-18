# -*- coding: utf-8 -*-
from __future__ import annotations

"""POS line-grid schema.

The POS screen is touch/cashier-oriented, but it must use the same column schema
concept used by transaction documents.  This keeps column keys, required-column
rules, presets, i18n labels, and future restaurant/POS alignment consistent.
"""

from features.transactions.grids.transaction_column_schema import TransactionColumn


def pos_line_schema() -> list[TransactionColumn]:
    return [
        TransactionColumn("row", "#", True, True, True, 46, editable=False),
        TransactionColumn("barcode", "transaction_column_barcode", False, True, False, 140, editable=False),
        TransactionColumn("item", "transaction_column_item", True, True, True, 280, True, editable=False),
        TransactionColumn("unit", "transaction_column_unit", False, True, True, 95, editable=False),
        TransactionColumn("qty", "transaction_column_qty", True, True, True, 95, numeric=True, editable=False),
        TransactionColumn("base_qty", "pos_column_base_qty", False, False, False, 110, numeric=True, editable=False),
        TransactionColumn("price", "transaction_column_price", False, True, True, 120, numeric=True, editable=False),
        TransactionColumn("total", "transaction_column_total", True, True, True, 130, numeric=True, editable=False),
        TransactionColumn("available", "transaction_column_available", False, True, False, 110, numeric=True, editable=False),
        TransactionColumn("barcode_scope", "pos_column_barcode_scope", False, False, False, 120, editable=False),
    ]
