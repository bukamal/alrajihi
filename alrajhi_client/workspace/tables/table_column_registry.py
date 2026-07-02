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


def _list_column(key: str, label_key: str | None = None, *, required: bool = False, visible: bool = True,
                 printable: bool = True, exportable: bool = True, width: int = 120,
                 data_type: str | None = None, alignment: str | None = None) -> ColumnDefinition:
    dtype = data_type or _type_for_key(key)
    align = alignment or _align_for_key(key, dtype in {"money", "quantity", "number"})
    return ColumnDefinition(
        key=key,
        label_key=label_key or key,
        visible_default=bool(visible or required),
        printable_default=bool(printable),
        exportable_default=bool(exportable),
        width=int(width or 120),
        alignment=align,
        data_type=dtype,
        editable=False,
        required=bool(required),
    )


def _columns(keys: tuple[str, ...], *, required: tuple[str, ...] = (), hidden: tuple[str, ...] = (),
             money: tuple[str, ...] = (), quantity: tuple[str, ...] = (), dates: tuple[str, ...] = (),
             widths: Mapping[str, int] | None = None) -> tuple[ColumnDefinition, ...]:
    widths = dict(widths or {})
    result = []
    for key in keys:
        if key in money:
            dtype = "money"
        elif key in quantity:
            dtype = "quantity"
        elif key in dates or key.endswith("_date") or key in {"date", "created_at", "last_login", "timestamp", "opened", "closed"}:
            dtype = "date"
        elif key in {"status", "workflow_status", "is_default", "default"}:
            dtype = "status"
        elif key in {"barcode", "code", "number", "ref", "reference", "invoice", "return_no"}:
            dtype = "text"
        else:
            dtype = None
        result.append(_list_column(
            key,
            key,
            required=key in required,
            visible=key not in hidden,
            printable=key not in hidden,
            exportable=True,
            width=widths.get(key, 140),
            data_type=dtype,
            alignment="start" if key in {"name", "item", "description", "notes", "address", "details", "party", "customer", "supplier"} else None,
        ))
    return tuple(result)


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
    _transaction_column("cost", "transaction_column_price", width=110, numeric=True),
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

# Phase 343: runtime application sweep for the remaining long-lived list,
# report and operational tables that still used only legacy SmartTable identity
# persistence.  These contracts intentionally mirror GenericTableModel
# data_keys used by the existing widgets so display/print/export settings can be
# applied without changing data services or view models.
MATERIALS_LIST_COLUMNS = (
    ColumnDefinition("name", "material_list_column_name", True, True, True, 220, "start", "text", False, True),
    ColumnDefinition("barcode", "material_list_column_barcode", True, True, True, 150, "center", "barcode"),
    ColumnDefinition("category", "material_list_column_category", True, True, True, 150, "center", "text"),
    ColumnDefinition("item_type", "material_list_column_type", True, True, True, 120, "center", "text"),
    ColumnDefinition("quantity", "material_list_column_opening_qty", True, True, True, 110, "right", "quantity"),
    ColumnDefinition("unit", "material_list_column_unit", True, True, True, 90, "center", "text"),
    ColumnDefinition("sold_quantity", "material_list_column_sold_qty", True, True, True, 110, "right", "quantity"),
    ColumnDefinition("available_quantity", "material_list_column_available_qty", True, True, True, 130, "right", "quantity", False, True),
    ColumnDefinition("stock_status", "material_list_column_stock_status", True, True, True, 120, "center", "status"),
    ColumnDefinition("reorder_level", "material_list_column_reorder_level", True, True, True, 120, "right", "quantity"),
    ColumnDefinition("available_total", "material_list_column_stock_value", True, True, True, 130, "right", "money"),
    ColumnDefinition("unit_cost", "material_list_column_unit_cost", True, True, True, 120, "right", "money"),
)
PARTY_LIST_COLUMNS = _columns(("name", "phone", "address", "balance"), required=("name",), money=("balance",), widths={"name": 220, "address": 260})
CATEGORY_LIST_COLUMNS = _columns(("full_name", "parent_name", "item_count", "child_count", "status", "description"), required=("full_name",), quantity=("item_count", "child_count"), widths={"full_name": 240, "description": 260})
BRANCH_LIST_COLUMNS = _columns(("name", "code", "address", "phone", "warehouse_count", "is_default", "status", "notes"), required=("name",), quantity=("warehouse_count",), widths={"name": 220, "address": 260, "notes": 240})
USER_LIST_COLUMNS = _columns(("username", "full_name", "role", "branch", "created_at", "last_login"), required=("username",), dates=("created_at", "last_login"), widths={"username": 180, "full_name": 220})
VOUCHER_LIST_COLUMNS = _columns(("date", "type", "party", "amount", "account", "description"), required=("date", "amount"), money=("amount",), dates=("date",), widths={"party": 220, "description": 260})
INVOICE_LIST_COLUMNS = _columns(("reference", "invoice", "invoice_total", "customer", "received", "remaining", "workflow_status", "invoice_profit", "date", "notes"), required=("invoice", "invoice_total"), money=("invoice_total", "received", "remaining", "invoice_profit"), dates=("date",), widths={"customer": 220, "notes": 240})
PURCHASE_INVOICE_LIST_COLUMNS = _columns(("reference", "invoice", "invoice_total", "supplier", "paid", "remaining", "workflow_status", "date", "notes"), required=("invoice", "invoice_total"), money=("invoice_total", "paid", "remaining"), dates=("date",), widths={"supplier": 220, "notes": 240})
RETURN_LIST_COLUMNS = _columns(("reference", "return_no", "original_invoice", "customer", "return_total", "refund", "settlement_remaining", "date", "notes"), required=("return_no", "return_total"), money=("return_total", "refund", "settlement_remaining"), dates=("date",), widths={"customer": 220, "notes": 240})
PURCHASE_RETURN_LIST_COLUMNS = _columns(("reference", "return_no", "original_invoice", "supplier", "return_total", "refund", "settlement_remaining", "date", "notes"), required=("return_no", "return_total"), money=("return_total", "refund", "settlement_remaining"), dates=("date",), widths={"supplier": 220, "notes": 240})
WAREHOUSE_LIST_COLUMNS = _columns(("name", "code", "branch", "manager", "phone", "address", "status", "notes"), required=("name",), widths={"name": 220, "address": 260, "notes": 240})
WAREHOUSE_BALANCE_COLUMNS = _columns(("item", "variant", "warehouse", "quantity", "available", "reorder_level", "status"), required=("item", "quantity"), quantity=("quantity", "available", "reorder_level"), widths={"item": 260, "variant": 160})
WAREHOUSE_MOVEMENT_COLUMNS = _columns(("date", "warehouse", "item", "variant", "type", "quantity", "reference", "notes"), required=("date", "item", "quantity"), quantity=("quantity",), dates=("date",), widths={"item": 260, "notes": 240})
WAREHOUSE_TRANSFER_COLUMNS = _columns(("date", "from_warehouse", "to_warehouse", "item", "variant", "quantity", "status", "reference", "notes"), required=("date", "item", "quantity"), quantity=("quantity",), dates=("date",), widths={"item": 260, "notes": 240})
CASHBOX_LIST_COLUMNS = _columns(("branch", "name", "code", "balance", "default", "status"), required=("name",), money=("balance",), widths={"name": 220})
BANK_LIST_COLUMNS = _columns(("branch", "bank", "account", "number", "balance", "status"), required=("bank", "account"), money=("balance",), widths={"bank": 190, "account": 220})
SHIFT_LIST_COLUMNS = _columns(("id", "branch", "cashbox", "opened", "closed", "status", "sales", "diff"), required=("id",), money=("sales", "diff"), dates=("opened", "closed"), widths={"cashbox": 200})
CASH_MOVEMENT_COLUMNS = _columns(("date", "branch", "account", "type", "amount", "ref", "desc"), required=("date", "amount"), money=("amount",), dates=("date",), widths={"desc": 260})
AUDIT_EVENT_COLUMNS = _columns(("username", "action", "entity_type", "entity_id", "details", "source", "ip_address", "timestamp"), required=("action", "timestamp"), dates=("timestamp",), widths={"details": 320})
MANUFACTURING_BOM_COLUMNS = _columns(("reference", "product", "version", "status", "components", "cost", "date", "notes"), required=("product",), money=("cost",), quantity=("components",), dates=("date",), widths={"product": 260})
MANUFACTURING_ORDER_COLUMNS = _columns(("reference", "product", "quantity", "status", "planned_date", "completed_date", "cost", "notes"), required=("product", "quantity"), money=("cost",), quantity=("quantity",), dates=("planned_date", "completed_date"), widths={"product": 260})
REPORT_RESULT_COLUMNS = _columns(("date", "reference", "name", "description", "amount", "debit", "credit", "balance", "status", "notes"), money=("amount", "debit", "credit", "balance"), dates=("date",), widths={"description": 280, "notes": 240})
GENERIC_OPERATION_COLUMNS = _columns(("name", "status", "updated_at", "notes"), required=("name",), dates=("updated_at",), widths={"name": 240, "notes": 260})
APPAREL_MATRIX_COLUMNS = _columns(("color", "size", "barcode", "sku", "quantity", "sale_price", "cost_price"), required=("color", "size"), money=("sale_price", "cost_price"), quantity=("quantity",), widths={"barcode": 170, "sku": 150})
BATCH_BARCODE_COLUMNS = _columns(("id", "name", "barcode", "price", "details", "copies"), required=("name", "barcode"), money=("price",), quantity=("copies",), widths={"name": 240, "details": 280})

RESTAURANT_SIMPLE_INVOICE_COLUMNS = _columns(
    ("item", "quantity", "price", "total", "notes"),
    required=("item", "quantity", "total"),
    money=("price", "total"),
    quantity=("quantity",),
    widths={"item": 260, "notes": 220},
)
RESTAURANT_MENU_CATEGORY_COLUMNS = _columns(
    ("id", "name", "code", "item_count", "status", "notes"),
    required=("name",),
    quantity=("item_count",),
    widths={"name": 220, "notes": 240},
)
RESTAURANT_MENU_ITEM_COLUMNS = _columns(
    ("id", "name", "category", "barcode", "price", "station", "status", "notes"),
    required=("name", "price"),
    money=("price",),
    widths={"name": 240, "category": 180, "barcode": 170, "notes": 240},
)

TABLE_COLUMN_CONTRACTS: Mapping[str, TableColumnContract] = {
    contract_id("sales_invoices", "lines"): _contract("sales_invoices", "lines", "editable_line", SALES_INVOICE_LINE_COLUMNS, editable=True),
    contract_id("purchase_invoices", "lines"): _contract("purchase_invoices", "lines", "editable_line", PURCHASE_INVOICE_LINE_COLUMNS, editable=True),
    contract_id("returns", "lines"): _contract("returns", "lines", "editable_line", RETURN_COMMON_COLUMNS, editable=True),
    contract_id("purchase_returns", "lines"): _contract("purchase_returns", "lines", "editable_line", RETURN_COMMON_COLUMNS, editable=True),
    contract_id("sales_invoices", "list"): _contract("sales_invoices", "list", "read_only_list", INVOICE_LIST_COLUMNS),
    contract_id("purchase_invoices", "list"): _contract("purchase_invoices", "list", "read_only_list", PURCHASE_INVOICE_LIST_COLUMNS),
    contract_id("returns", "list"): _contract("returns", "list", "read_only_list", RETURN_LIST_COLUMNS),
    contract_id("purchase_returns", "list"): _contract("purchase_returns", "list", "read_only_list", PURCHASE_RETURN_LIST_COLUMNS),
    contract_id("items", "materials"): _contract("items", "materials", "read_only_list", MATERIALS_LIST_COLUMNS),
    contract_id("categories", "categories"): _contract("categories", "categories", "read_only_list", CATEGORY_LIST_COLUMNS),
    contract_id("customers", "customers"): _contract("customers", "customers", "read_only_list", PARTY_LIST_COLUMNS),
    contract_id("suppliers", "suppliers"): _contract("suppliers", "suppliers", "read_only_list", PARTY_LIST_COLUMNS),
    contract_id("branches", "branches"): _contract("branches", "branches", "read_only_list", BRANCH_LIST_COLUMNS),
    contract_id("users", "users"): _contract("users", "users", "read_only_list", USER_LIST_COLUMNS),
    contract_id("vouchers", "voucher_lines"): _contract("vouchers", "voucher_lines", "editable_line", VOUCHER_LIST_COLUMNS, editable=True),
    contract_id("vouchers", "list"): _contract("vouchers", "list", "read_only_list", VOUCHER_LIST_COLUMNS),
    contract_id("warehouses", "warehouses"): _contract("warehouses", "warehouses", "read_only_list", WAREHOUSE_LIST_COLUMNS),
    contract_id("warehouses", "balances"): _contract("warehouses", "balances", "read_only_list", WAREHOUSE_BALANCE_COLUMNS),
    contract_id("warehouses", "movements"): _contract("warehouses", "movements", "read_only_list", WAREHOUSE_MOVEMENT_COLUMNS),
    contract_id("warehouses", "transfers"): _contract("warehouses", "transfers", "read_only_list", WAREHOUSE_TRANSFER_COLUMNS),
    contract_id("cashboxes", "cashboxes"): _contract("cashboxes", "cashboxes", "read_only_list", CASHBOX_LIST_COLUMNS),
    contract_id("cashboxes", "banks"): _contract("cashboxes", "banks", "read_only_list", BANK_LIST_COLUMNS),
    contract_id("cashboxes", "shifts"): _contract("cashboxes", "shifts", "read_only_list", SHIFT_LIST_COLUMNS),
    contract_id("cashboxes", "movements"): _contract("cashboxes", "movements", "read_only_list", CASH_MOVEMENT_COLUMNS),
    contract_id("manufacturing", "orders"): _contract("manufacturing", "orders", "read_only_list", MANUFACTURING_ORDER_COLUMNS),
    contract_id("manufacturing", "bom"): _contract("manufacturing", "bom", "read_only_list", MANUFACTURING_BOM_COLUMNS),
    contract_id("reports", "result"): _contract("reports", "result", "report", REPORT_RESULT_COLUMNS),
    contract_id("audit_log", "events"): _contract("audit_log", "events", "report", AUDIT_EVENT_COLUMNS),
    contract_id("offline_queue", "queue"): _contract("offline_queue", "queue", "operational", GENERIC_OPERATION_COLUMNS),
    contract_id("monitoring", "health"): _contract("monitoring", "health", "operational", GENERIC_OPERATION_COLUMNS),
    contract_id("apparel", "variants"): _contract("apparel", "variants", "read_only_list", APPAREL_VARIANT_COLUMNS),
    contract_id("apparel", "matrix"): _contract("apparel", "matrix", "matrix", APPAREL_MATRIX_COLUMNS, editable=True),
    contract_id("apparel", "reports"): _contract("apparel", "reports", "report", APPAREL_REPORT_COLUMNS),
    contract_id("pos", "lines"): _contract("pos", "lines", "operational_line", POS_LINE_COLUMNS, printable=True, exportable=True),
    contract_id("restaurant", "simple_invoice_lines"): _contract("restaurant", "simple_invoice_lines", "operational_line", RESTAURANT_SIMPLE_INVOICE_COLUMNS, editable=True, printable=True, exportable=True),
    contract_id("restaurant", "menu_categories"): _contract("restaurant", "menu_categories", "operational_list", RESTAURANT_MENU_CATEGORY_COLUMNS, printable=True, exportable=True),
    contract_id("restaurant", "menu_items"): _contract("restaurant", "menu_items", "operational_list", RESTAURANT_MENU_ITEM_COLUMNS, printable=True, exportable=True),
    contract_id("restaurant", "order_lines"): _contract("restaurant", "order_lines", "operational_line", RESTAURANT_ORDER_LINE_COLUMNS, printable=True, exportable=True),
    contract_id("restaurant", "kds_tickets"): _contract("restaurant", "kds_tickets", "operational_board", RESTAURANT_KDS_TICKET_COLUMNS, printable=True, exportable=True),
    contract_id("restaurant", "kds_lines"): _contract("restaurant", "kds_lines", "operational_board", RESTAURANT_KDS_LINE_COLUMNS, printable=True, exportable=True),
    contract_id("restaurant", "kitchen_queue"): _contract("restaurant", "kitchen_queue", "operational_board", RESTAURANT_KDS_TICKET_COLUMNS, printable=True, exportable=True),
    contract_id("restaurant", "tables"): _contract("restaurant", "tables", "operational_board", _columns(("table", "zone", "guests", "status", "notes"), required=("table",), quantity=("guests",)), printable=True, exportable=True),
    contract_id("cafe", "order_lines"): _contract("cafe", "order_lines", "operational_line", CAFE_ORDER_LINE_COLUMNS, printable=True, exportable=True),
    contract_id("cafe", "preparation_tickets"): _contract("cafe", "preparation_tickets", "operational_board", RESTAURANT_KDS_TICKET_COLUMNS, printable=True, exportable=True),
    contract_id("cafe", "preparation_lines"): _contract("cafe", "preparation_lines", "operational_board", RESTAURANT_KDS_LINE_COLUMNS, printable=True, exportable=True),
    contract_id("cafe", "preparation_queue"): _contract("cafe", "preparation_queue", "operational_board", RESTAURANT_KDS_TICKET_COLUMNS, printable=True, exportable=True),
    contract_id("cafe", "shift_report"): _contract("cafe", "shift_report", "report", _columns(("date", "orders", "sales", "discount", "tax", "cash", "card", "notes"), money=("sales", "discount", "tax", "cash", "card"), quantity=("orders",), dates=("date",)), printable=True, exportable=True),
    contract_id("batch_print", "labels"): _contract("batch_print", "labels", "operational", BATCH_BARCODE_COLUMNS),
}



TABLE_IDENTITY_CONTRACTS: Mapping[str, str] = {
    "materials.workspace.items_grid": "items.materials",
    "ItemsWidget.main": "items.materials",
    "categories.list": "categories.categories",
    "CategoriesWidget.main": "categories.categories",
    "customers": "customers.customers",
    "CustomersWidget.main": "customers.customers",
    "suppliers": "suppliers.suppliers",
    "SuppliersWidget.main": "suppliers.suppliers",
    "users.list": "users.users",
    "UsersWidget.main": "users.users",
    "vouchers.list": "vouchers.list",
    "VouchersWidget.main": "vouchers.list",
    "branches.list": "branches.branches",
    "BranchesWidget.main": "branches.branches",
    "InvoicesWidget.sales": "sales_invoices.list",
    "InvoicesWidget.purchases": "purchase_invoices.list",
    "returns.list": "returns.list",
    "ReturnsWidget.sales_returns": "returns.list",
    "PurchaseReturnsWidget.purchase_returns": "purchase_returns.list",
    "warehouses.list": "warehouses.warehouses",
    "warehouses.balances": "warehouses.balances",
    "warehouses.movements": "warehouses.movements",
    "warehouses.transfers": "warehouses.transfers",
    "cashboxes.cashboxes": "cashboxes.cashboxes",
    "cashboxes.banks": "cashboxes.banks",
    "cashboxes.shifts": "cashboxes.shifts",
    "cashboxes.movements": "cashboxes.movements",
    "manufacturing.workspace.bom": "manufacturing.bom",
    "manufacturing.workspace.orders": "manufacturing.orders",
    "audit_log.list": "audit_log.events",
    "reports.result": "reports.result",
    "batch_print.items.default": "batch_print.labels",
    "batch_print.apparel.variant_labels": "batch_print.labels",
    "restaurant.simple.invoice": "restaurant.simple_invoice_lines",
    "restaurant.menu.categories": "restaurant.menu_categories",
    "restaurant.menu.items": "restaurant.menu_items",
    "batch_print.restaurant.menu_items": "batch_print.labels",
    "batch_print.restaurant.table_labels": "batch_print.labels",
    "batch_print.cafe.products": "batch_print.labels",
    "batch_print.cafe.modifier_labels": "batch_print.labels",
}


def contract_id_for_identity(identity: str) -> str:
    return TABLE_IDENTITY_CONTRACTS.get(str(identity or ""), "")


def table_column_contract_for_identity(identity: str) -> TableColumnContract | None:
    cid = contract_id_for_identity(identity)
    return table_column_contract_by_id(cid) if cid else None


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
