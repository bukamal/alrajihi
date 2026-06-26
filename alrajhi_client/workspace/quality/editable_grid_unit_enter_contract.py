# -*- coding: utf-8 -*-
"""Static contract for Phase385 editable-grid unit traversal.

The purpose is narrow and runtime-oriented: after committing material/item or
barcode in an editable document grid, Enter must move to the unit column first
when that column is visible/editable, then continue to quantity.  Quantity is
only the fallback when unit is unavailable.
"""
from __future__ import annotations

from pathlib import Path

FILES = {
    "keyboard": "alrajhi_client/ui/table_keyboard_policy.py",
    "transaction_schema": "alrajhi_client/features/transactions/grids/transaction_column_schema.py",
    "inventory_schema": "alrajhi_client/features/inventory/grids/inventory_transfer_schema.py",
    "manufacturing_schema": "alrajhi_client/features/manufacturing/grids/manufacturing_column_schema.py",
    "transaction_grid": "alrajhi_client/features/transactions/grids/transaction_line_grid.py",
}

REQUIRED_MARKERS = {
    "keyboard": (
        "Phase385 refines the operational sequence to item/barcode -> unit -> quantity",
        "_standard_unit_entry_keys = (\"unit\", \"uom\", \"unit_name\")",
        "Phase385 ERP line-entry flow is material/barcode -> unit -> quantity.",
        "unit_cols = self._standard_columns_matching_keys(start.row(), self._standard_unit_entry_keys)",
        "if unit_cols:\n            return self._standard_model().index(start.row(), unit_cols[0])",
        "qty_cols = self._standard_columns_matching_keys(start.row(), self._standard_quantity_entry_keys)",
        "If the unit column is hidden or locked, the fallback remains quantity.",
    ),
    "transaction_schema": (
        'TransactionColumn("unit", "transaction_column_unit"',
        'TransactionColumn("qty", "transaction_column_qty"',
        'TransactionColumn("qty", "transaction_column_return_qty"',
    ),
    "inventory_schema": (
        "TransactionColumn('unit', 'transaction_column_unit'",
        "TransactionColumn('qty', 'transaction_column_qty'",
    ),
    "manufacturing_schema": (
        "ManufacturingColumn('unit', 'transaction_column_unit'",
        "ManufacturingColumn('qty', 'manufacturing_column_component_qty'",
    ),
    "transaction_grid": (
        "TransactionUnitDelegate",
        "self.setItemDelegateForColumn(unit_col, TransactionUnitDelegate(self))",
    ),
}

FORBIDDEN_MARKERS = {
    "keyboard": (
        "The ERP line-entry flow is material/barcode -> quantity.  Unit and price",
        "item resolver should not land on technical/read-mostly columns",
    ),
}

ORDER_CHECKS = {
    "keyboard": (
        (
            "unit_cols = self._standard_columns_matching_keys(start.row(), self._standard_unit_entry_keys)",
            "qty_cols = self._standard_columns_matching_keys(start.row(), self._standard_quantity_entry_keys)",
            "post-commit must test unit before quantity",
        ),
    ),
    "transaction_schema": (
        ('TransactionColumn("unit", "transaction_column_unit"', 'TransactionColumn("qty", "transaction_column_qty"', "sales/purchase unit precedes quantity"),
        ('TransactionColumn("unit", "transaction_column_unit"', 'TransactionColumn("qty", "transaction_column_return_qty"', "return unit precedes quantity"),
    ),
    "inventory_schema": (
        ("TransactionColumn('unit', 'transaction_column_unit'", "TransactionColumn('qty', 'transaction_column_qty'", "transfer unit precedes quantity"),
    ),
    "manufacturing_schema": (
        ("ManufacturingColumn('unit', 'transaction_column_unit'", "ManufacturingColumn('qty', 'manufacturing_column_component_qty'", "BOM unit precedes quantity"),
    ),
}


def _read(root: Path, rel: str) -> str:
    try:
        return (root / rel).read_text(encoding="utf-8")
    except Exception:
        return ""


def editable_grid_unit_enter_matrix(root: Path | str) -> list[dict[str, str]]:
    base = Path(root)
    rows: list[dict[str, str]] = []
    for key, rel in FILES.items():
        path = base / rel
        text = _read(base, rel)
        rows.append({"key": "file_exists", "target": rel, "status": "pass" if path.exists() else "fail", "detail": key, "phase": "385"})
        for marker in REQUIRED_MARKERS.get(key, ()):  # type: ignore[arg-type]
            rows.append({
                "key": marker[:96],
                "target": rel,
                "status": "pass" if marker in text else "fail",
                "detail": "required marker present" if marker in text else marker,
                "phase": "385",
            })
        for marker in FORBIDDEN_MARKERS.get(key, ()):  # type: ignore[arg-type]
            rows.append({
                "key": marker[:96],
                "target": rel,
                "status": "pass" if marker not in text else "fail",
                "detail": "forbidden marker absent" if marker not in text else marker,
                "phase": "385",
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
                "phase": "385",
            })
    return rows


def editable_grid_unit_enter_summary(root: Path | str) -> dict[str, int | bool]:
    rows = editable_grid_unit_enter_matrix(root)
    issues = sum(1 for row in rows if row.get("status") != "pass")
    return {"phase": 385, "checks": len(rows), "issues": issues, "ready": issues == 0}
