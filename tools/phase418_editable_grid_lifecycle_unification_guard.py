#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "audit_outputs" / "editable_grid_lifecycle_unification_matrix.csv"


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def add(rows: list[dict[str, str]], key: str, category: str, path: str, ok: bool, detail: str) -> None:
    rows.append({
        "key": key,
        "category": category,
        "path": path,
        "status": "OK" if ok else "FAIL",
        "detail": detail,
    })


def _has_lifecycle_api(source: str) -> bool:
    return all(needle in source for needle in (
        "def is_empty_line",
        "def trim_extra_trailing_empty_lines",
        "def ensure_single_trailing_empty_line",
        "def add_empty_line",
        "return self.ensure_single_trailing_empty_line()",
    ))


def main() -> int:
    rows: list[dict[str, str]] = []
    required = [
        "PHASE418_EDITABLE_GRID_LIFECYCLE_UNIFICATION.md",
        "alrajhi_client/workspace/quality/editable_grid_lifecycle_unification_contract.py",
        "tools/phase418_editable_grid_lifecycle_unification_guard.py",
        "tests/test_phase418_editable_grid_lifecycle_unification.py",
    ]
    for rel in required:
        add(rows, f"exists::{rel}", "file", rel, (ROOT / rel).exists(), "required Phase418 file exists")

    doc = read("PHASE418_EDITABLE_GRID_LIFECYCLE_UNIFICATION.md")
    contract = read("alrajhi_client/workspace/quality/editable_grid_lifecycle_unification_contract.py")
    policy = read("alrajhi_client/features/transactions/grids/unified_grid_navigation_policy.py")
    keyboard = read("alrajhi_client/ui/table_keyboard_policy.py")
    tx_model = read("alrajhi_client/features/transactions/grids/transaction_line_model.py")
    inventory_model = read("alrajhi_client/features/inventory/grids/inventory_transfer_lines_model.py")
    bom_model = read("alrajhi_client/features/manufacturing/grids/bom_components_model.py")
    item_editor = read("alrajhi_client/features/items/item_editor_tab.py")
    release = read("alrajhi_client/workspace/quality/release_gate_contract.py")

    add(rows, "doc_phase", "doc", "PHASE418_EDITABLE_GRID_LIFECYCLE_UNIFICATION.md", "Phase 418" in doc and "Editable Grid Lifecycle Unification" in doc, "phase documentation exists")
    add(rows, "contract_phase", "contract", "alrajhi_client/workspace/quality/editable_grid_lifecycle_unification_contract.py", "EDITABLE_GRID_LIFECYCLE_UNIFICATION_CONTRACT" in contract and '"phase": 418' in contract, "contract declares phase 418")

    add(rows, "transaction_lifecycle_api", "model", "alrajhi_client/features/transactions/grids/transaction_line_model.py", _has_lifecycle_api(tx_model), "transaction lines expose idempotent lifecycle API")
    add(rows, "inventory_lifecycle_api", "model", "alrajhi_client/features/inventory/grids/inventory_transfer_lines_model.py", _has_lifecycle_api(inventory_model), "inventory transfer lines expose idempotent lifecycle API")
    add(rows, "bom_lifecycle_api", "model", "alrajhi_client/features/manufacturing/grids/bom_components_model.py", _has_lifecycle_api(bom_model), "BOM component lines expose idempotent lifecycle API")

    add(rows, "inventory_empty_qty_zero", "model", "alrajhi_client/features/inventory/grids/inventory_transfer_lines_model.py", "'qty': Decimal('0')" in inventory_model and "'base_qty': Decimal('0')" in inventory_model, "blank transfer row is truly empty")
    add(rows, "inventory_add_item_reuses_tail", "model", "alrajhi_client/features/inventory/grids/inventory_transfer_lines_model.py", "not self.is_empty_line(len(self.lines) - 1)" in inventory_model and "self.ensure_single_trailing_empty_line()" in inventory_model, "lookup add reuses trailing blank row")
    add(rows, "bom_add_item_reuses_tail", "model", "alrajhi_client/features/manufacturing/grids/bom_components_model.py", "not self.is_empty_line(len(self.lines) - 1)" in bom_model and "self.ensure_single_trailing_empty_line()" in bom_model, "BOM add_item reuses trailing blank row")

    for name in ("INVENTORY_TRANSFER_ROUTE", "BOM_COMPONENT_ROUTE", "MATERIAL_UNIT_ROUTE"):
        add(rows, f"policy_{name.lower()}", "policy", "alrajhi_client/features/transactions/grids/unified_grid_navigation_policy.py", name in policy, f"{name} is declared")
    for key in ("inventory_transfer", "warehouse_transfer", "bom_components", "material_units"):
        add(rows, f"policy_document_{key}", "policy", "alrajhi_client/features/transactions/grids/unified_grid_navigation_policy.py", f'"{key}"' in policy, f"{key} has a route")

    add(rows, "keyboard_bom_route", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "BOM/manufacturing component documents" in keyboard and "waste_percent" in keyboard and "total_cost" in keyboard, "keyboard policy recognizes BOM route")
    add(rows, "keyboard_inventory_route", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "Inventory transfers" in keyboard and "base_qty" in keyboard and "available" in keyboard, "keyboard policy recognizes transfer route")
    add(rows, "keyboard_model_gate", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "ensure_callback = getattr(target, \"ensure_single_trailing_empty_line\", None)" in keyboard, "keyboard delegates row creation to model gate")

    add(rows, "material_units_manual_add", "materials", "alrajhi_client/features/items/item_editor_tab.py", "self.add_unit_btn.clicked.connect(self.add_unit_row)" in item_editor and "def add_unit_row" in item_editor, "material unit rows are explicit user actions")
    add(rows, "material_units_no_auto_enter_append", "materials", "alrajhi_client/features/items/item_editor_tab.py", "returnPressed.connect(self.add_unit_row)" not in item_editor and "cellChanged.connect(self.add_unit_row)" not in item_editor, "material units do not auto-append on Enter/change")

    add(rows, "release_gate_doc", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "PHASE418_EDITABLE_GRID_LIFECYCLE_UNIFICATION" in release, "Phase418 doc registered in release gate")
    add(rows, "release_gate_test", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "tests/test_phase418_editable_grid_lifecycle_unification.py" in release, "Phase418 test registered in release gate")
    add(rows, "release_gate_check", "release", "alrajhi_client/workspace/quality/release_gate_contract.py", "editable_grid_lifecycle_unification" in release and "phase=418" in release, "Phase418 release check registered")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "path", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    failures = [row for row in rows if row["status"] != "OK"]
    print(f"Phase418 editable grid lifecycle unification checks: {len(rows)} checks, failures={len(failures)}")
    for row in failures:
        print(f"FAIL {row['key']}: {row['detail']}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
