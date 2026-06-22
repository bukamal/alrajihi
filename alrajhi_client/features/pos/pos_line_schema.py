# -*- coding: utf-8 -*-
from __future__ import annotations

"""POS line-grid schema.

The POS screen is touch/cashier-oriented, but it must use the same universal
column contract used by transaction documents and operational restaurant/cafe
screens.  Phase 335 binds POS display/print/export columns to the central
registry while preserving the legacy TransactionColumn consumer API.
"""

from features.transactions.grids.transaction_column_schema import TransactionColumn
from features.transactions.grids.universal_column_adapter import transaction_columns_from_contract


def _fallback_pos_line_schema() -> list[TransactionColumn]:
    return [
        TransactionColumn("row", "#", True, True, True, 46, editable=False),
        TransactionColumn("barcode", "transaction_column_barcode", False, True, False, 140, editable=False),
        TransactionColumn("item", "transaction_column_item", True, True, True, 280, True, editable=False),
        TransactionColumn("variant", "transaction_column_variant", False, False, False, 120, editable=False),
        TransactionColumn("unit", "transaction_column_unit", False, True, True, 95, editable=False),
        TransactionColumn("qty", "transaction_column_qty", True, True, True, 95, numeric=True, editable=False),
        TransactionColumn("base_qty", "pos_column_base_qty", False, False, False, 110, numeric=True, editable=False),
        TransactionColumn("price", "transaction_column_price", False, True, True, 120, numeric=True, editable=False),
        TransactionColumn("total", "transaction_column_total", True, True, True, 130, numeric=True, editable=False),
        TransactionColumn("available", "transaction_column_available", False, True, False, 110, numeric=True, editable=False),
        TransactionColumn("barcode_scope", "pos_column_barcode_scope", False, False, False, 120, editable=False),
    ]


def pos_line_schema() -> list[TransactionColumn]:
    return transaction_columns_from_contract("pos", "lines", _fallback_pos_line_schema())
