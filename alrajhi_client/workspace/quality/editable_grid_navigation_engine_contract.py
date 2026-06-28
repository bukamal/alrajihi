# -*- coding: utf-8 -*-
"""Phase412 unified editable grid navigation engine contract.

This import-safe contract protects the operator Enter/Shift+Enter workflow in
all editable ERP grids.  It focuses on behaviour rather than visual styling:
there must be one owner for Enter traversal, no local invoice walker, no silent
field clearing, and no duplicate empty rows at the end of an entry grid.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]

EDITABLE_GRID_NAVIGATION_ENGINE_CONTRACT = {
    "phase": 412,
    "name": "editable_grid_navigation_engine",
    "scope": (
        "TransactionLineGrid, EditableSmartGrid, legacy invoice lines, inventory transfer lines, "
        "manufacturing/BOM grids and delegates"
    ),
    "problem": (
        "Multiple Enter handlers and delegate commits could skip business columns, clear existing cell data, "
        "or append more than one trailing row."
    ),
    "requirements": (
        "StandardTableKeyboardMixin is the single Enter/Shift+Enter navigation owner for editable grids.",
        "Legacy invoice_dialog Enter filtering must defer to TransactionLineGrid instead of using physical column walking.",
        "Enter navigation must be re-entrant safe and cannot execute twice for the same editor close.",
        "Leaving the end of a row must reuse an existing empty tail row or append exactly one row.",
        "Duplicate trailing empty rows must be trimmed defensively.",
        "Transaction item delegates may not clear existing values on Enter unless the operator actually edited the text to empty.",
        "Combo delegates must not commit while loading editor data through currentIndexChanged.",
        "Semantic routes cover invoices, returns, inventory transfers and BOM/manufacturing grids.",
    ),
    "required_outputs": (
        "tools/audit_outputs/editable_grid_navigation_engine_matrix.csv",
    ),
    "acceptance_rule": (
        "A complete Enter walk through an editable grid follows visible business columns, preserves existing values, "
        "and leaves at most one reusable empty line at the tail."
    ),
}


def _read(rel: str, root: Path | None = None) -> str:
    base = root or ROOT
    path = base / rel
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def editable_grid_navigation_engine_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    checks = [
        ("phase_doc", "doc", "PHASE412_EDITABLE_GRID_NAVIGATION_ENGINE.md", "Phase 412"),
        ("contract", "contract", "alrajhi_client/workspace/quality/editable_grid_navigation_engine_contract.py", "EDITABLE_GRID_NAVIGATION_ENGINE_CONTRACT"),
        ("single_trailing_gate", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "def _standard_ensure_single_trailing_empty_line"),
        ("append_reentrant_guard", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "_standard_enter_append_guard"),
        ("enter_reentrant_guard", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "_standard_enter_navigation_active"),
        ("trim_extra_tail_rows", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "def _standard_trim_extra_trailing_empty_lines"),
        ("row_empty_detector", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "def _standard_row_is_empty_for_append"),
        ("return_route", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "Return documents: material -> unit -> returned qty"),
        ("inventory_route", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "Inventory transfers: material -> unit -> qty -> notes"),
        ("bom_route", "keyboard", "alrajhi_client/ui/table_keyboard_policy.py", "BOM/manufacturing component documents"),
        ("legacy_invoice_delegates_enter", "legacy_invoice", "alrajhi_client/views/dialogs/invoice_dialog.py", "return False\n"),
        ("legacy_invoice_no_physical_enter_call", "legacy_invoice", "alrajhi_client/views/dialogs/invoice_dialog.py", "Phase412: Enter traversal is owned by TransactionLineGrid"),
        ("item_delegate_user_edited", "delegate", "alrajhi_client/features/transactions/grids/transaction_item_delegate.py", "_transaction_item_user_edited"),
        ("item_delegate_no_enter_clear", "delegate", "alrajhi_client/features/transactions/grids/transaction_item_delegate.py", "Enter navigation must never wipe an existing item"),
        ("combo_delegate_activated", "delegate", "alrajhi_client/views/dialogs/invoice_delegates.py", "combo.activated.connect"),
        ("guard_tool", "tool", "tools/phase412_editable_grid_navigation_engine_guard.py", "Phase412 editable grid navigation engine"),
        ("phase_test", "test", "tests/test_phase412_editable_grid_navigation_engine.py", "test_phase412"),
    ]
    rows: List[Dict[str, object]] = []
    for check, category, rel, needle in checks:
        content = _read(rel, base)
        ok = bool(content) and needle in content
        rows.append({
            "check": check,
            "category": category,
            "path": rel,
            "needle": needle,
            "status": "OK" if ok else "FAIL",
            "detail": "" if ok else f"missing {needle!r}",
        })
    return rows


def editable_grid_navigation_engine_summary(root: Path | None = None) -> Dict[str, object]:
    rows = editable_grid_navigation_engine_matrix(root)
    failures = [row for row in rows if row["status"] != "OK"]
    return {
        "phase": 412,
        "checks": len(rows),
        "issues": len(failures),
        "ready": not failures,
    }


def required_outputs() -> tuple[str, ...]:
    return tuple(EDITABLE_GRID_NAVIGATION_ENGINE_CONTRACT["required_outputs"])
