from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..i18n import tr

@dataclass(frozen=True)
class TransactionColumn:
    key: str
    title_key: str
    required: bool = False
    default_visible: bool = True
    compact_visible: bool = False
    width: int = 120
    stretch: bool = False
    editable: bool = True
    numeric: bool = False

    @property
    def title(self) -> str:
        return tr(self.title_key)

SchemaFactory = Callable[[], list[TransactionColumn]]


def sales_invoice_schema() -> list[TransactionColumn]:
    return [
        TransactionColumn("row", "#", True, True, True, 44),
        TransactionColumn("barcode", "transaction_column_barcode", False, True, False, 120),
        TransactionColumn("item", "transaction_column_item", True, True, True, 260, True),
        TransactionColumn("variant", "transaction_column_variant", False, True, False, 130, editable=False),
        TransactionColumn("unit", "transaction_column_unit", False, True, True, 90),
        TransactionColumn("qty", "transaction_column_qty", True, True, True, 90, numeric=True),
        TransactionColumn("available", "transaction_column_available", False, True, False, 90, numeric=True, editable=False),
        TransactionColumn("price", "transaction_column_price", False, True, True, 110, numeric=True),
        TransactionColumn("discount", "transaction_column_discount", False, True, False, 90, numeric=True),
        TransactionColumn("tax", "transaction_column_tax", False, True, False, 90, numeric=True),
        TransactionColumn("total", "transaction_column_total", True, True, True, 120, numeric=True, editable=False),
        TransactionColumn("notes", "transaction_column_notes", False, True, False, 180),
    ]


def purchase_invoice_schema() -> list[TransactionColumn]:
    return [
        TransactionColumn("row", "#", True, True, True, 44),
        TransactionColumn("barcode", "transaction_column_barcode", False, True, False, 120),
        TransactionColumn("item", "transaction_column_item", True, True, True, 260, True),
        TransactionColumn("variant", "transaction_column_variant", False, True, False, 130, editable=False),
        TransactionColumn("unit", "transaction_column_unit", False, True, True, 90),
        TransactionColumn("qty", "transaction_column_qty", True, True, True, 90, numeric=True),
        TransactionColumn("cost", "transaction_column_cost", False, True, True, 110, numeric=True),
        TransactionColumn("batch", "transaction_column_batch", False, True, False, 120),
        TransactionColumn("expiry", "transaction_column_expiry", False, True, False, 120),
        TransactionColumn("discount", "transaction_column_discount", False, True, False, 90, numeric=True),
        TransactionColumn("tax", "transaction_column_tax", False, True, False, 90, numeric=True),
        TransactionColumn("total", "transaction_column_total", True, True, True, 120, numeric=True, editable=False),
        TransactionColumn("notes", "transaction_column_notes", False, True, False, 180),
    ]


def sales_return_schema() -> list[TransactionColumn]:
    return [
        TransactionColumn("row", "#", True, True, True, 44, editable=False),
        TransactionColumn("original_invoice", "transaction_column_original_invoice", False, True, False, 145, editable=False),
        TransactionColumn("barcode", "transaction_column_barcode", False, True, False, 120, editable=False),
        TransactionColumn("item", "transaction_column_item", True, True, True, 260, True, editable=False),
        TransactionColumn("variant", "transaction_column_variant", False, True, False, 130, editable=False),
        TransactionColumn("original_qty", "transaction_column_sold_qty", False, True, False, 90, numeric=True, editable=False),
        TransactionColumn("previous_qty", "transaction_column_previous_return", False, True, False, 100, numeric=True, editable=False),
        TransactionColumn("returnable_qty", "transaction_column_returnable", False, True, False, 110, numeric=True, editable=False),
        TransactionColumn("unit", "transaction_column_unit", False, True, True, 90),
        TransactionColumn("qty", "transaction_column_return_qty", True, True, True, 110, numeric=True),
        TransactionColumn("reason", "transaction_column_reason", False, True, False, 150),
        TransactionColumn("restock", "transaction_column_restock", False, True, False, 120),
        TransactionColumn("price", "transaction_column_unit_value", False, True, True, 110, numeric=True, editable=False),
        TransactionColumn("total", "transaction_column_total", True, True, True, 120, numeric=True, editable=False),
        TransactionColumn("notes", "transaction_column_notes", False, True, False, 180),
    ]


def purchase_return_schema() -> list[TransactionColumn]:
    return [
        TransactionColumn("row", "#", True, True, True, 44, editable=False),
        TransactionColumn("original_invoice", "transaction_column_original_invoice", False, True, False, 145, editable=False),
        TransactionColumn("barcode", "transaction_column_barcode", False, True, False, 120, editable=False),
        TransactionColumn("item", "transaction_column_item", True, True, True, 260, True, editable=False),
        TransactionColumn("variant", "transaction_column_variant", False, True, False, 130, editable=False),
        TransactionColumn("original_qty", "transaction_column_purchased_qty", False, True, False, 90, numeric=True, editable=False),
        TransactionColumn("previous_qty", "transaction_column_previous_return", False, True, False, 100, numeric=True, editable=False),
        TransactionColumn("returnable_qty", "transaction_column_returnable", False, True, False, 110, numeric=True, editable=False),
        TransactionColumn("unit", "transaction_column_unit", False, True, True, 90),
        TransactionColumn("qty", "transaction_column_return_qty", True, True, True, 110, numeric=True),
        TransactionColumn("reason", "transaction_column_reason", False, True, False, 150),
        TransactionColumn("price", "transaction_column_unit_value", False, True, True, 110, numeric=True, editable=False),
        TransactionColumn("total", "transaction_column_total", True, True, True, 120, numeric=True, editable=False),
        TransactionColumn("notes", "transaction_column_notes", False, True, False, 180),
    ]


def schema_for(document_type: str) -> list[TransactionColumn]:
    if document_type == "purchase_invoice":
        return purchase_invoice_schema()
    if document_type == "sales_return":
        return sales_return_schema()
    if document_type == "purchase_return":
        return purchase_return_schema()
    return sales_invoice_schema()
