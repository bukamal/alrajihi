# -*- coding: utf-8 -*-
"""Static contract for Phase386 invoice Enter traversal.

Daily invoice entry must follow a semantic business route, not the physical
column order.  For purchase invoices the storage field remains ``cost`` for
accounting compatibility, but the operator-facing header is ``price`` and Enter
moves through: material -> unit -> quantity -> price -> discount -> tax -> total
-> notes.  Sales invoices move through material -> unit -> quantity -> price ->
discount -> total -> notes.  Navigation must not clear existing cell values.
"""
from __future__ import annotations

from pathlib import Path

FILES = {
    "keyboard": "alrajhi_client/ui/table_keyboard_policy.py",
    "transaction_schema": "alrajhi_client/features/transactions/grids/transaction_column_schema.py",
    "table_registry": "alrajhi_client/workspace/tables/table_column_registry.py",
}

PURCHASE_ROUTE = 'return [("item", "material", "product", "barcode"), ("unit", "uom", "unit_name"), ("qty", "quantity"), ("cost", "price"), ("discount",), ("tax",), ("total",), ("notes",)]'
SALES_ROUTE = 'return [("item", "material", "product", "barcode"), ("unit", "uom", "unit_name"), ("qty", "quantity"), ("price",), ("discount",), ("total",), ("notes",)]'

REQUIRED_MARKERS = {
    "keyboard": (
        "Phase386 replaces physical-column Enter walking in sales/purchase invoices",
        "def _standard_business_route_slots(self) -> list[tuple[str, ...]]:",
        "The route is deliberately semantic, not physical.",
        PURCHASE_ROUTE,
        SALES_ROUTE,
        "def _standard_next_business_route_index(self, start: QModelIndex, forward: bool = True) -> QModelIndex:",
        "route_target = self._standard_next_business_route_index(start, forward=forward)",
        "route_target = self._standard_next_business_route_index(start, forward=True)",
        "ordered_wanted = [str(key or \"\").casefold() for key in slot]",
        "initial Enter path must start at the material column, not at barcode",
        "it never\n  clears existing values merely because the operator is moving through the row",
    ),
    "transaction_schema": (
        'TransactionColumn("item", "transaction_column_item"',
        'TransactionColumn("unit", "transaction_column_unit"',
        'TransactionColumn("qty", "transaction_column_qty"',
        'TransactionColumn("cost", "transaction_column_price", False, True, True, 110, numeric=True)',
        'TransactionColumn("discount", "transaction_column_discount"',
        'TransactionColumn("tax", "transaction_column_tax"',
        'TransactionColumn("total", "transaction_column_total"',
        'TransactionColumn("notes", "transaction_column_notes"',
    ),
    "table_registry": (
        '_transaction_column("cost", "transaction_column_price", width=110, numeric=True)',
    ),
}

FORBIDDEN_MARKERS = {
    "transaction_schema": (
        'TransactionColumn("cost", "transaction_column_cost", False, True, True, 110, numeric=True)',
    ),
    "table_registry": (
        '_transaction_column("cost", "transaction_column_cost", width=110, numeric=True),\n    _transaction_column("batch"',
    ),
    "keyboard": (
        "route must start at barcode",
        "clear existing values merely because focus moved",
    ),
}

ORDER_CHECKS = {
    "keyboard": (
        ("def _standard_business_route_slots", "def _standard_next_business_route_index", "route slots declared before route traversal"),
        ("ordered_wanted", "if self._standard_is_traversable(index):\n                    return col", "alias order is respected before choosing a route column"),
        ("route_target = self._standard_next_business_route_index(start, forward=True)", "unit_cols = self._standard_columns_matching_keys(start.row(), self._standard_unit_entry_keys)", "business route is preferred before legacy unit fallback"),
        (PURCHASE_ROUTE, SALES_ROUTE, "purchase and sales routes are both declared"),
    ),
    "transaction_schema": (
        ('TransactionColumn("item", "transaction_column_item"', 'TransactionColumn("unit", "transaction_column_unit"', "item before unit"),
        ('TransactionColumn("unit", "transaction_column_unit"', 'TransactionColumn("qty", "transaction_column_qty"', "unit before quantity"),
        ('TransactionColumn("qty", "transaction_column_qty"', 'TransactionColumn("cost", "transaction_column_price"', "quantity before purchase price/cost"),
        ('TransactionColumn("discount", "transaction_column_discount"', 'TransactionColumn("tax", "transaction_column_tax"', "discount before tax"),
        ('TransactionColumn("tax", "transaction_column_tax"', 'TransactionColumn("total", "transaction_column_total"', "tax before total"),
        ('TransactionColumn("total", "transaction_column_total"', 'TransactionColumn("notes", "transaction_column_notes"', "total before notes"),
    ),
}


def _read(root: Path, rel: str) -> str:
    try:
        return (root / rel).read_text(encoding="utf-8")
    except Exception:
        return ""


def editable_grid_invoice_enter_route_matrix(root: Path | str) -> list[dict[str, str]]:
    base = Path(root)
    rows: list[dict[str, str]] = []
    for key, rel in FILES.items():
        path = base / rel
        text = _read(base, rel)
        rows.append({"key": "file_exists", "target": rel, "status": "pass" if path.exists() else "fail", "detail": key, "phase": "386"})
        for marker in REQUIRED_MARKERS.get(key, ()):  # type: ignore[arg-type]
            rows.append({
                "key": marker[:96],
                "target": rel,
                "status": "pass" if marker in text else "fail",
                "detail": "required marker present" if marker in text else marker,
                "phase": "386",
            })
        for marker in FORBIDDEN_MARKERS.get(key, ()):  # type: ignore[arg-type]
            rows.append({
                "key": marker[:96],
                "target": rel,
                "status": "pass" if marker not in text else "fail",
                "detail": "forbidden marker absent" if marker not in text else marker,
                "phase": "386",
            })
        for first, second, detail in ORDER_CHECKS.get(key, ()):  # type: ignore[arg-type]
            first_pos = text.find(first)
            second_pos = text.find(second)
            ok = first_pos >= 0 and second_pos >= 0 and first_pos < second_pos
            rows.append({
                "key": f"order::{detail}",
                "target": rel,
                "status": "pass" if ok else "fail",
                "detail": detail,
                "phase": "386",
            })
    return rows


def editable_grid_invoice_enter_route_summary(root: Path | str) -> dict[str, int | bool]:
    rows = editable_grid_invoice_enter_route_matrix(root)
    issues = sum(1 for row in rows if row.get("status") != "pass")
    return {"phase": 386, "checks": len(rows), "issues": issues, "ready": issues == 0}
