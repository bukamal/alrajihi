# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Iterable

from workspace.tables import table_column_contract
from .transaction_column_schema import TransactionColumn


def _is_numeric(data_type: str) -> bool:
    return str(data_type or "").lower() in {"money", "quantity", "number"}


def transaction_column_from_definition(column) -> TransactionColumn:
    return TransactionColumn(
        key=column.key,
        title_key=column.label_key,
        required=bool(column.required),
        default_visible=bool(column.visible_default or column.required),
        compact_visible=bool(column.required or column.key in {"row", "item", "qty", "total", "status"}),
        width=int(column.width or 120),
        stretch=column.key in {"item", "modifiers", "notes"},
        editable=bool(column.editable),
        numeric=_is_numeric(column.data_type),
        printable_default=bool(column.printable_default),
        exportable_default=bool(column.exportable_default),
    )


def transaction_columns_from_contract(page_id: str, table_id: str, fallback: Iterable[TransactionColumn]) -> list[TransactionColumn]:
    contract = table_column_contract(page_id, table_id)
    if not contract:
        return list(fallback or [])
    return [transaction_column_from_definition(column) for column in contract.columns]
