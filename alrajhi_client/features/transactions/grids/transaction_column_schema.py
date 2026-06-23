from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from workspace.tables import ColumnDefinition, table_column_contract

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
    printable_default: bool = True
    exportable_default: bool = True

    @property
    def title(self) -> str:
        return tr(self.title_key)

    @property
    def data_type(self) -> str:
        if self.key in {"price", "cost", "discount", "tax", "total"}:
            return "money"
        if self.key in {"qty", "available", "original_qty", "previous_qty", "returnable_qty"}:
            return "quantity"
        return "number" if self.numeric else "text"

    @property
    def alignment(self) -> str:
        if self.numeric or self.data_type in {"money", "quantity", "number"}:
            return "right"
        if self.key in {"item", "notes", "reason"}:
            return "start"
        return "center"

    def to_column_definition(self, table_settings_prefix: str = "") -> ColumnDefinition:
        return ColumnDefinition(
            key=self.key,
            label_key=self.title_key,
            visible_default=bool(self.default_visible or self.required),
            printable_default=bool(self.printable_default),
            exportable_default=bool(self.exportable_default),
            width=int(self.width or 120),
            alignment=self.alignment,
            data_type=self.data_type,
            editable=bool(self.editable),
            required=bool(self.required),
        ).scoped(table_settings_prefix)

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
        TransactionColumn("original_invoice", "transaction_column_original_invoice", False, False, False, 145, editable=False),
        TransactionColumn("barcode", "transaction_column_barcode", False, True, False, 120),
        TransactionColumn("item", "transaction_column_item", True, True, True, 260, True),
        TransactionColumn("variant", "transaction_column_variant", False, True, False, 130, editable=False),
        TransactionColumn("original_qty", "transaction_column_sold_qty", False, True, False, 90, numeric=True, editable=False),
        TransactionColumn("previous_qty", "transaction_column_previous_return", False, True, False, 100, numeric=True, editable=False),
        TransactionColumn("returnable_qty", "transaction_column_returnable", False, True, False, 110, numeric=True, editable=False),
        TransactionColumn("unit", "transaction_column_unit", False, True, True, 90),
        TransactionColumn("qty", "transaction_column_return_qty", True, True, True, 110, numeric=True),
        TransactionColumn("reason", "transaction_column_reason", False, True, False, 150),
        TransactionColumn("restock", "transaction_column_restock", False, True, False, 120),
        TransactionColumn("price", "transaction_column_unit_value", False, True, True, 110, numeric=True),
        TransactionColumn("total", "transaction_column_total", True, True, True, 120, numeric=True, editable=False),
        TransactionColumn("notes", "transaction_column_notes", False, True, False, 180),
    ]


def purchase_return_schema() -> list[TransactionColumn]:
    return [
        TransactionColumn("row", "#", True, True, True, 44, editable=False),
        TransactionColumn("original_invoice", "transaction_column_original_invoice", False, False, False, 145, editable=False),
        TransactionColumn("barcode", "transaction_column_barcode", False, True, False, 120),
        TransactionColumn("item", "transaction_column_item", True, True, True, 260, True),
        TransactionColumn("variant", "transaction_column_variant", False, True, False, 130, editable=False),
        TransactionColumn("original_qty", "transaction_column_purchased_qty", False, True, False, 90, numeric=True, editable=False),
        TransactionColumn("previous_qty", "transaction_column_previous_return", False, True, False, 100, numeric=True, editable=False),
        TransactionColumn("returnable_qty", "transaction_column_returnable", False, True, False, 110, numeric=True, editable=False),
        TransactionColumn("unit", "transaction_column_unit", False, True, True, 90),
        TransactionColumn("qty", "transaction_column_return_qty", True, True, True, 110, numeric=True),
        TransactionColumn("reason", "transaction_column_reason", False, True, False, 150),
        TransactionColumn("price", "transaction_column_unit_value", False, True, True, 110, numeric=True),
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


def _page_table_for_document(document_type: str) -> tuple[str, str]:
    mapping = {
        "sales_invoice": ("sales_invoices", "lines"),
        "purchase_invoice": ("purchase_invoices", "lines"),
        "sales_return": ("returns", "lines"),
        "purchase_return": ("purchase_returns", "lines"),
    }
    return mapping.get(document_type, ("sales_invoices", "lines"))


def universal_contract_for_document(document_type: str):
    page_id, table_id = _page_table_for_document(document_type)
    return table_column_contract(page_id, table_id)


def universal_columns_for_document(document_type: str) -> tuple[ColumnDefinition, ...]:
    contract = universal_contract_for_document(document_type)
    if contract:
        return contract.columns
    prefix = f"ui/columns/transactions/{document_type}"
    return tuple(col.to_column_definition(prefix) for col in schema_for(document_type))
