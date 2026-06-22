# -*- coding: utf-8 -*-
"""Project table-column contracts.

This registry intentionally starts with the highest-risk tables and expands
operational screens through the same display/print/export contract: invoices,
POS, restaurant, cafe and apparel.
"""
from __future__ import annotations

from typing import Mapping

from .column_contract import ColumnDefinition, TableColumnContract, contract_id, scoped_columns


def _type_for_key(key: str, numeric: bool = False) -> str:
    if key in {"price", "cost", "discount", "tax", "total", "sale_price", "paid", "remaining"}:
        return "money"
    if key in {"qty", "available", "original_qty", "previous_qty", "returnable_qty", "quantity", "reorder_level", "base_qty", "line_count", "guests"}:
        return "quantity"
    if key in {"expiry", "date"}:
        return "date"
    return "number" if numeric else "text"


def _align_for_key(key: str, numeric: bool = False) -> str:
    if numeric or _type_for_key(key) in {"money", "quantity", "number"}:
        return "right"
    if key in {"item", "notes", "reason", "modifiers", "table", "station"}:
        return "start"
    return "center"


def _transaction_column(key: str, label_key: str, *, required: bool = False, visible: bool = True,
                        printable: bool = True, exportable: bool = True, width: int = 120,
                        stretch: bool = False, editable: bool = True, numeric: bool = False) -> ColumnDefinition:
    return ColumnDefinition(
        key=key,
        label_key=label_key,
        visible_default=bool(visible or required),
        printable_default=bool(printable),
        exportable_default=bool(exportable),
        width=int(width or 120),
        alignment=_align_for_key(key, numeric),
        data_type=_type_for_key(key, numeric),
        editable=bool(editable),
        required=bool(required),
    )


def _contract(page_id: str, table_id: str, table_type: str, columns: tuple[ColumnDefinition, ...], *, editable: bool = False, printable: bool = True, exportable: bool = True) -> TableColumnContract:
    prefix = f"ui/columns/{page_id}/{table_id}"
    return TableColumnContract(
        page_id=page_id,
        table_id=table_id,
        table_type=table_type,
        settings_prefix=prefix,
        columns=scoped_columns(columns, prefix),
        editable=editable,
        printable=printable,
        exportable=exportable,
    )


SALES_INVOICE_LINE_COLUMNS: tuple[ColumnDefinition, ...] = (
    _transaction_column("row", "#", required=True, width=44, editable=False, numeric=True),
    _transaction_column("barcode", "transaction_column_barcode", width=120),
    _transaction_column("item", "transaction_column_item", required=True, width=260, stretch=True),
    _transaction_column("variant", "transaction_column_variant", width=130, editable=False),
    _transaction_column("unit", "transaction_column_unit", width=90),
    _transaction_column("qty", "transaction_column_qty", required=True, width=90, numeric=True),
    _transaction_column("available", "transaction_column_available", width=90, numeric=True, editable=False),
    _transaction_column("price", "transaction_column_price", width=110, numeric=True),
    _transaction_column("discount", "transaction_column_discount", width=90, numeric=True),
    _transaction_column("tax", "transaction_column_tax", width=90, numeric=True),
    _transaction_column("total", "transaction_column_total", required=True, width=120, numeric=True, editable=False),
    _transaction_column("notes", "transaction_column_notes", width=180),
)

PURCHASE_INVOICE_LINE_COLUMNS: tuple[ColumnDefinition, ...] = (
    _transaction_column("row", "#", required=True, width=44, editable=False, numeric=True),
    _transaction_column("barcode", "transaction_column_barcode", width=120),
    _transaction_column("item", "transaction_column_item", required=True, width=260, stretch=True),
    _transaction_column("variant", "transaction_column_variant", width=130, editable=False),
    _transaction_column("unit", "transaction_column_unit", width=90),
    _transaction_column("qty", "transaction_column_qty", required=True, width=90, numeric=True),
    _transaction_column("cost", "transaction_column_cost", width=110, numeric=True),
    _transaction_column("batch", "transaction_column_batch", width=120),
    _transaction_column("expiry", "transaction_column_expiry", width=120),
    _transaction_column("discount", "transaction_column_discount", width=90, numeric=True),
    _transaction_column("tax", "transaction_column_tax", width=90, numeric=True),
    _transaction_column("total", "transaction_column_total", required=True, width=120, numeric=True, editable=False),
    _transaction_column("notes", "transaction_column_notes", width=180),
)

RETURN_COMMON_COLUMNS: tuple[ColumnDefinition, ...] = (
    _transaction_column("row", "#", required=True, width=44, editable=False, numeric=True),
    _transaction_column("original_invoice", "transaction_column_original_invoice", width=145, editable=False),
    _transaction_column("barcode", "transaction_column_barcode", width=120, editable=False),
    _transaction_column("item", "transaction_column_item", required=True, width=260, stretch=True, editable=False),
    _transaction_column("variant", "transaction_column_variant", width=130, editable=False),
    _transaction_column("original_qty", "transaction_column_sold_qty", width=90, numeric=True, editable=False),
    _transaction_column("previous_qty", "transaction_column_previous_return", width=100, numeric=True, editable=False),
    _transaction_column("returnable_qty", "transaction_column_returnable", width=110, numeric=True, editable=False),
    _transaction_column("unit", "transaction_column_unit", width=90),
    _transaction_column("qty", "transaction_column_return_qty", required=True, width=110, numeric=True),
    _transaction_column("reason", "transaction_column_reason", width=150),
    _transaction_column("restock", "transaction_column_restock", width=120),
    _transaction_column("price", "transaction_column_unit_value", width=110, numeric=True, editable=False),
    _transaction_column("total", "transaction_column_total", required=True, width=120, numeric=True, editable=False),
    _transaction_column("notes", "transaction_column_notes", width=180),
)

APPAREL_VARIANT_COLUMNS: tuple[ColumnDefinition, ...] = (
    ColumnDefinition("item", "apparel_col_item", True, True, True, 220, "start", "text", False, True),
    ColumnDefinition("color", "apparel_col_color", True, True, True, 110, "center", "text"),
    ColumnDefinition("size", "apparel_col_size", True, True, True, 90, "center", "text"),
    ColumnDefinition("sku", "apparel_col_sku", True, True, True, 130, "center", "text"),
    ColumnDefinition("barcode", "apparel_col_barcode", True, True, True, 150, "center", "barcode"),
    ColumnDefinition("quantity", "apparel_col_quantity", True, True, True, 110, "right", "quantity"),
    ColumnDefinition("reorder_level", "apparel_col_reorder_level", True, True, True, 120, "right", "quantity"),
    ColumnDefinition("sale_price", "apparel_col_sale_price", True, True, True, 120, "right", "money"),
    ColumnDefinition("status", "apparel_col_status", True, False, True, 110, "center", "status"),
)

APPAREL_REPORT_COLUMNS: tuple[ColumnDefinition, ...] = (
    ColumnDefinition("item", "apparel_col_item", True, True, True, 220, "start", "text"),
    ColumnDefinition("color", "apparel_col_color", True, True, True, 110, "center", "text"),
    ColumnDefinition("size", "apparel_col_size", True, True, True, 90, "center", "text"),
    ColumnDefinition("quantity", "apparel_col_quantity", True, True, True, 110, "right", "quantity"),
    ColumnDefinition("reorder_level", "apparel_col_reorder_level", True, True, True, 120, "right", "quantity"),
    ColumnDefinition("sku", "apparel_col_sku", True, True, True, 130, "center", "text"),
)

POS_LINE_COLUMNS: tuple[ColumnDefinition, ...] = (
    ColumnDefinition("row", "#", True, True, True, 46, "center", "number", False, True),
    ColumnDefinition("barcode", "transaction_column_barcode", False, True, False, 140, "center", "barcode"),
    ColumnDefinition("item", "transaction_column_item", True, True, True, 280, "start", "text", False, True),
    ColumnDefinition("variant", "transaction_column_variant", False, False, False, 120, "center", "text"),
    ColumnDefinition("unit", "transaction_column_unit", False, True, True, 95, "center", "text"),
    ColumnDefinition("qty", "transaction_column_qty", True, True, True, 95, "right", "quantity", False, True),
    ColumnDefinition("base_qty", "pos_column_base_qty", False, False, False, 110, "right", "quantity"),
    ColumnDefinition("price", "transaction_column_price", False, True, True, 120, "right", "money"),
    ColumnDefinition("total", "transaction_column_total", True, True, True, 130, "right", "money", False, True),
    ColumnDefinition("available", "transaction_column_available", False, True, False, 110, "right", "quantity"),
    ColumnDefinition("barcode_scope", "pos_column_barcode_scope", False, False, False, 120, "center", "text"),
)

RESTAURANT_ORDER_LINE_COLUMNS: tuple[ColumnDefinition, ...] = (
    ColumnDefinition("row", "#", True, True, True, 46, "center", "number", False, True),
    ColumnDefinition("item", "transaction_column_item", True, True, True, 280, "start", "text", False, True),
    ColumnDefinition("modifiers", "restaurant_column_modifiers", False, False, False, 170, "start", "text"),
    ColumnDefinition("unit", "transaction_column_unit", False, False, True, 95, "center", "text"),
    ColumnDefinition("qty", "transaction_column_qty", True, True, True, 95, "right", "quantity", False, True),
    ColumnDefinition("base_qty", "pos_column_base_qty", False, False, False, 110, "right", "quantity"),
    ColumnDefinition("price", "transaction_column_price", False, True, True, 120, "right", "money"),
    ColumnDefinition("total", "transaction_column_total", True, True, True, 130, "right", "money", False, True),
    ColumnDefinition("status", "restaurant_column_status", False, False, True, 135, "center", "status"),
    ColumnDefinition("barcode_scope", "pos_column_barcode_scope", False, False, False, 125, "center", "text"),
    ColumnDefinition("notes", "transaction_column_notes", False, False, False, 180, "start", "text"),
)

CAFE_ORDER_LINE_COLUMNS: tuple[ColumnDefinition, ...] = (
    ColumnDefinition("row", "#", True, True, True, 46, "center", "number", False, True),
    ColumnDefinition("item", "transaction_column_item", True, True, True, 280, "start", "text", False, True),
    ColumnDefinition("modifiers", "restaurant_column_modifiers", True, True, True, 190, "start", "text"),
    ColumnDefinition("unit", "transaction_column_unit", False, False, True, 95, "center", "text"),
    ColumnDefinition("qty", "transaction_column_qty", True, True, True, 95, "right", "quantity", False, True),
    ColumnDefinition("price", "transaction_column_price", False, True, True, 120, "right", "money"),
    ColumnDefinition("total", "transaction_column_total", True, True, True, 130, "right", "money", False, True),
    ColumnDefinition("status", "restaurant_column_status", True, True, True, 135, "center", "status"),
    ColumnDefinition("notes", "transaction_column_notes", True, True, True, 180, "start", "text"),
)

RESTAURANT_KDS_TICKET_COLUMNS: tuple[ColumnDefinition, ...] = (
    ColumnDefinition("ticket", "restaurant.kds.ticket", True, True, True, 90, "center", "number", False, True),
    ColumnDefinition("table", "restaurant.table", True, True, True, 150, "start", "text"),
    ColumnDefinition("station", "restaurant.kds.station", True, True, True, 150, "start", "text"),
    ColumnDefinition("line_count", "restaurant.lines_count", True, True, True, 110, "right", "quantity"),
    ColumnDefinition("status", "restaurant_column_status", True, True, True, 130, "center", "status"),
    ColumnDefinition("elapsed_minutes", "restaurant.kds.minutes", True, True, True, 120, "right", "number"),
)

RESTAURANT_KDS_LINE_COLUMNS: tuple[ColumnDefinition, ...] = (
    ColumnDefinition("item", "transaction_column_item", True, True, True, 260, "start", "text", False, True),
    ColumnDefinition("qty", "transaction_column_qty", True, True, True, 95, "right", "quantity", False, True),
    ColumnDefinition("modifiers", "restaurant_column_modifiers", True, True, True, 190, "start", "text"),
    ColumnDefinition("notes", "transaction_column_notes", True, True, True, 220, "start", "text"),
)

TABLE_COLUMN_CONTRACTS: Mapping[str, TableColumnContract] = {
    contract_id("sales_invoices", "lines"): _contract("sales_invoices", "lines", "editable_line", SALES_INVOICE_LINE_COLUMNS, editable=True),
    contract_id("purchase_invoices", "lines"): _contract("purchase_invoices", "lines", "editable_line", PURCHASE_INVOICE_LINE_COLUMNS, editable=True),
    contract_id("returns", "lines"): _contract("returns", "lines", "editable_line", RETURN_COMMON_COLUMNS, editable=True),
    contract_id("purchase_returns", "lines"): _contract("purchase_returns", "lines", "editable_line", RETURN_COMMON_COLUMNS, editable=True),
    contract_id("apparel", "variants"): _contract("apparel", "variants", "read_only_list", APPAREL_VARIANT_COLUMNS),
    contract_id("apparel", "reports"): _contract("apparel", "reports", "report", APPAREL_REPORT_COLUMNS),
    contract_id("pos", "lines"): _contract("pos", "lines", "operational_line", POS_LINE_COLUMNS, printable=True, exportable=True),
    contract_id("restaurant", "order_lines"): _contract("restaurant", "order_lines", "operational_line", RESTAURANT_ORDER_LINE_COLUMNS, printable=True, exportable=True),
    contract_id("restaurant", "kds_tickets"): _contract("restaurant", "kds_tickets", "operational_board", RESTAURANT_KDS_TICKET_COLUMNS, printable=True, exportable=True),
    contract_id("restaurant", "kds_lines"): _contract("restaurant", "kds_lines", "operational_board", RESTAURANT_KDS_LINE_COLUMNS, printable=True, exportable=True),
    contract_id("cafe", "order_lines"): _contract("cafe", "order_lines", "operational_line", CAFE_ORDER_LINE_COLUMNS, printable=True, exportable=True),
    contract_id("cafe", "preparation_tickets"): _contract("cafe", "preparation_tickets", "operational_board", RESTAURANT_KDS_TICKET_COLUMNS, printable=True, exportable=True),
    contract_id("cafe", "preparation_lines"): _contract("cafe", "preparation_lines", "operational_board", RESTAURANT_KDS_LINE_COLUMNS, printable=True, exportable=True),
}


def table_column_contract(page_id: str, table_id: str) -> TableColumnContract | None:
    return TABLE_COLUMN_CONTRACTS.get(contract_id(page_id, table_id))


def table_column_contract_by_id(cid: str) -> TableColumnContract | None:
    return TABLE_COLUMN_CONTRACTS.get(str(cid or ""))


def contract_ids() -> tuple[str, ...]:
    return tuple(sorted(TABLE_COLUMN_CONTRACTS.keys()))


def columns_for_table(page_id: str, table_id: str) -> tuple[ColumnDefinition, ...]:
    contract = table_column_contract(page_id, table_id)
    return contract.columns if contract else tuple()


def default_visible_keys(page_id: str, table_id: str) -> tuple[str, ...]:
    contract = table_column_contract(page_id, table_id)
    return contract.default_visible_keys() if contract else tuple()


def default_printable_keys(page_id: str, table_id: str) -> tuple[str, ...]:
    contract = table_column_contract(page_id, table_id)
    return contract.default_printable_keys() if contract else tuple()


def default_exportable_keys(page_id: str, table_id: str) -> tuple[str, ...]:
    contract = table_column_contract(page_id, table_id)
    return contract.default_exportable_keys() if contract else tuple()
