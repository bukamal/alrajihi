# -*- coding: utf-8 -*-
from __future__ import annotations

from features.transactions.grids.transaction_column_schema import TransactionColumn


def inventory_transfer_lines_schema() -> list[TransactionColumn]:
    """Unit-aware line schema for warehouse transfer documents."""
    return [
        TransactionColumn('row', '#', True, True, True, 44, editable=False),
        TransactionColumn('barcode', 'transaction_column_barcode', False, True, False, 130),
        TransactionColumn('item', 'transaction_column_item', True, True, True, 280, True),
        TransactionColumn('unit', 'transaction_column_unit', False, True, True, 95),
        TransactionColumn('qty', 'transaction_column_qty', True, True, True, 95, numeric=True),
        TransactionColumn('base_qty', 'inventory_transfer_column_base_qty', False, True, False, 105, numeric=True, editable=False),
        TransactionColumn('available', 'transaction_column_available', False, True, False, 105, numeric=True, editable=False),
        TransactionColumn('unit_cost', 'unit_cost', False, True, False, 110, numeric=True, editable=False),
        TransactionColumn('notes', 'transaction_column_notes', False, True, False, 180),
    ]
