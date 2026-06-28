#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "audit_outputs"
OUT_CSV = OUT_DIR / "editable_grid_navigation_engine_matrix.csv"

CHECKS = [
    ("phase_doc", "doc", "PHASE412_EDITABLE_GRID_NAVIGATION_ENGINE.md", "Phase 412"),
    ("contract", "contract", "alrajhi_client/workspace/quality/editable_grid_navigation_engine_contract.py", "EDITABLE_GRID_NAVIGATION_ENGINE_CONTRACT"),
    ("single_trailing_gate", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "def _standard_ensure_single_trailing_empty_line"),
    ("row_empty_detector", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "def _standard_row_is_empty_for_append"),
    ("trim_extra_tail_rows", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "def _standard_trim_extra_trailing_empty_lines"),
    ("append_reentrant_guard", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "_standard_enter_append_guard"),
    ("enter_reentrant_guard", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "_standard_enter_navigation_active"),
    ("returns_route", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "Return documents: material -> unit -> returned qty"),
    ("inventory_route", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "Inventory transfers: material -> unit -> qty -> notes"),
    ("bom_route", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "BOM/manufacturing component documents"),
    ("item_delegate_user_edited", "delegate", "alrajhi_client/features/transactions/grids/transaction_item_delegate.py", "_transaction_item_user_edited"),
    ("item_delegate_preserve_empty_enter", "delegate", "alrajhi_client/features/transactions/grids/transaction_item_delegate.py", "if not user_edited and previous not in (None, \"\")"),
    ("combo_delegate_no_load_commit", "delegate", "alrajhi_client/views/dialogs/invoice_delegates.py", "combo.activated.connect"),
    ("legacy_invoice_enter_defers", "legacy_invoice", "alrajhi_client/views/dialogs/invoice_dialog.py", "Phase412: Enter traversal is owned by TransactionLineGrid"),
]


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _invoice_eventfilter_enter_ok(src: str) -> tuple[bool, str]:
    match = re.search(r"def eventFilter\(self, obj, event\):(.*?)(?:\n    def _move_to_next_invoice_cell|\n\n    def _move_to_next_invoice_cell)", src, flags=re.S)
    if not match:
        return False, "eventFilter body not found"
    body = match.group(1)
    if "_move_to_next_invoice_cell()" in body:
        return False, "legacy Enter still calls _move_to_next_invoice_cell inside eventFilter"
    if "key in (Qt.Key_Return, Qt.Key_Enter)" not in body or "return False" not in body:
        return False, "Enter branch does not defer to table view"
    return True, "legacy invoice Enter defers to TransactionLineGrid"


def _no_current_index_commit(src: str) -> tuple[bool, str]:
    forbidden = "currentIndexChanged.connect(lambda: self.commitData.emit(combo))"
    if forbidden in src:
        return False, "ItemComboDelegate still commits during setEditorData/currentIndexChanged"
    return True, "combo commit is activation/delegate-close driven"


def _append_sites_are_idempotent(src: str) -> tuple[bool, str]:
    route_body = re.search(r"def _standard_next_business_route_index\(.*?\n    def _standard_post_commit_index", src, flags=re.S)
    next_body = re.search(r"def _standard_next_index\(.*?\n    def _standard_editor_widget", src, flags=re.S)
    if not route_body or not next_body:
        return False, "navigation bodies not found"
    for name, body in (("business route", route_body.group(0)), ("generic route", next_body.group(0))):
        if "_standard_ensure_single_trailing_empty_line()" not in body:
            return False, f"{name} does not use idempotent trailing-line gate"
    return True, "both navigation exits use the idempotent trailing-line gate"


def main() -> int:
    rows: list[dict[str, str]] = []
    for check, category, rel, needle in CHECKS:
        content = read(rel)
        ok = bool(content) and needle in content
        rows.append({
            "check": check,
            "category": category,
            "path": rel,
            "needle": needle,
            "status": "OK" if ok else "FAIL",
            "detail": "" if ok else f"missing {needle!r}",
        })

    invoice_ok, invoice_detail = _invoice_eventfilter_enter_ok(read("alrajhi_client/views/dialogs/invoice_dialog.py"))
    rows.append({
        "check": "legacy_invoice_eventfilter_no_enter_walker",
        "category": "legacy_invoice",
        "path": "alrajhi_client/views/dialogs/invoice_dialog.py",
        "needle": "Enter branch does not call _move_to_next_invoice_cell",
        "status": "OK" if invoice_ok else "FAIL",
        "detail": invoice_detail,
    })

    combo_ok, combo_detail = _no_current_index_commit(read("alrajhi_client/views/dialogs/invoice_delegates.py"))
    rows.append({
        "check": "combo_delegate_no_currentindex_commit",
        "category": "delegate",
        "path": "alrajhi_client/views/dialogs/invoice_delegates.py",
        "needle": "no currentIndexChanged commitData lambda",
        "status": "OK" if combo_ok else "FAIL",
        "detail": combo_detail,
    })

    append_ok, append_detail = _append_sites_are_idempotent(read("alrajhi_client/ui/table_keyboard_policy.py"))
    rows.append({
        "check": "all_enter_append_sites_idempotent",
        "category": "keyboard",
        "path": "alrajhi_client/ui/table_keyboard_policy.py",
        "needle": "_standard_ensure_single_trailing_empty_line() in business and generic routes",
        "status": "OK" if append_ok else "FAIL",
        "detail": append_detail,
    })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "category", "path", "needle", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    failures = [row for row in rows if row["status"] != "OK"]
    if failures:
        print("Phase412 editable grid navigation engine failed:")
        for row in failures:
            print(f"- {row['check']}: {row['detail']}")
        return 1
    print(f"Phase412 editable grid navigation engine OK ({len(rows)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
