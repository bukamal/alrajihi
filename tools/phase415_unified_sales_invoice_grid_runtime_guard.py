# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "audit_outputs" / "unified_sales_invoice_grid_runtime_matrix.csv"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def add(rows: list[dict[str, str]], key: str, category: str, path: str, ok: bool, detail: str) -> None:
    rows.append({
        "key": key,
        "category": category,
        "path": path,
        "status": "OK" if ok else "FAIL",
        "detail": detail,
    })


def main() -> int:
    rows: list[dict[str, str]] = []
    policy_path = "alrajhi_client/features/transactions/grids/unified_grid_navigation_policy.py"
    model_path = "alrajhi_client/features/transactions/grids/transaction_line_model.py"
    grid_path = "alrajhi_client/features/transactions/grids/transaction_line_grid.py"
    keyboard_path = "alrajhi_client/ui/table_keyboard_policy.py"
    tab_path = "alrajhi_client/features/transactions/transaction_document_tab.py"
    release_path = "alrajhi_client/workspace/quality/release_gate_contract.py"

    for rel in [policy_path, model_path, grid_path, keyboard_path, tab_path, release_path, "PHASE415_UNIFIED_SALES_INVOICE_GRID_RUNTIME.md"]:
        add(rows, f"exists::{rel}", "file", rel, (ROOT / rel).exists(), "required file exists")

    policy = read(policy_path)
    model = read(model_path)
    grid = read(grid_path)
    keyboard = read(keyboard_path)
    tab = read(tab_path)
    release = read(release_path)

    add(rows, "sales_invoice_route_declared", "route", policy_path, "SALES_INVOICE_ROUTE" in policy and '"item",' in policy and '"unit",' in policy and '"qty",' in policy and '"price",' in policy and '"notes",' in policy, "semantic sales invoice route is declared")
    add(rows, "qt_free_navigation_policy", "route", policy_path, "PyQt5" not in policy and "QApplication" not in policy and "QModelIndex" not in policy, "navigation policy is PyQt-free")
    add(rows, "row_empty_predicate", "row_lifecycle", policy_path, "def is_empty_transaction_line" in policy and "IDENTITY_KEYS" in policy and "TEXT_IDENTITY_KEYS" in policy, "row emptiness is centralized")
    add(rows, "pure_trailing_gate", "row_lifecycle", policy_path, "def ensure_single_trailing_empty_line" in policy and "trim_extra_trailing_empty_lines" in policy, "pure idempotent trailing row gate exists")

    add(rows, "model_document_type", "model", model_path, "document_type: str = \"sales_invoice\"" in model and "self.document_type" in model, "model carries document type")
    add(rows, "model_owns_empty_detection", "model", model_path, "def is_empty_line" in model and "is_empty_transaction_line" in model, "model owns blank line detection")
    add(rows, "model_idempotent_gate", "model", model_path, "def ensure_single_trailing_empty_line" in model and "return self.ensure_single_trailing_empty_line()" in model, "add_empty_line is idempotent")
    add(rows, "model_loads_keep_single_tail", "model", model_path, model.count("self.ensure_single_trailing_empty_line()") >= 4, "loads/removes normalize the tail row")

    add(rows, "grid_overrides_edit", "editor", grid_path, "def edit(self, index, trigger=None, event=None)" in grid, "grid hooks every editor creation path")
    add(rows, "grid_installs_enter_filter_from_edit", "editor", grid_path, "_standard_prepare_active_editor" in grid and "QTimer.singleShot(0" in grid, "editor filter scheduled for AnyKeyPressed/double-click/programmatic edit")
    add(rows, "grid_no_qt_physical_enter", "editor", grid_path, "EditNextItem" not in grid and "EditPreviousItem" not in grid, "grid does not use Qt physical next/previous hints")

    add(rows, "keyboard_delegates_to_model_gate", "keyboard", keyboard_path, "ensure_callback = getattr(target, \"ensure_single_trailing_empty_line\", None)" in keyboard, "keyboard delegates append to model lifecycle gate")
    add(rows, "keyboard_keeps_phase412_guard", "keyboard", keyboard_path, "def _standard_ensure_single_trailing_empty_line" in keyboard and "_standard_enter_append_guard" in keyboard, "existing reentrancy guard remains")

    add(rows, "tab_passes_document_type", "wiring", tab_path, "TransactionLineModel(self.columns, self, document_type=self.context.document_type)" in tab, "document type is passed into model")
    add(rows, "release_gate_phase415_doc", "release", release_path, "PHASE415_UNIFIED_SALES_INVOICE_GRID_RUNTIME" in release, "phase 415 doc registered")
    add(rows, "release_gate_phase415_test", "release", release_path, "tests/test_phase415_unified_sales_invoice_grid_runtime.py" in release, "phase 415 test registered")
    add(rows, "release_gate_phase415_check", "release", release_path, "unified_sales_invoice_grid_runtime" in release and "phase=415" in release, "phase 415 release check registered")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "category", "path", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    failed = [row for row in rows if row["status"] != "OK"]
    print(f"Phase415 unified sales invoice grid runtime checks: {len(rows)} checks, failures={len(failed)}")
    for row in failed:
        print(f"FAIL {row['key']}: {row['detail']}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
