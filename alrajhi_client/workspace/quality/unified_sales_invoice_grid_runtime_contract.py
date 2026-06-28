# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

UNIFIED_SALES_INVOICE_GRID_RUNTIME_CONTRACT = {
    "phase": 415,
    "name": "unified_sales_invoice_grid_runtime",
    "scope": (
        "features.transactions.grids.TransactionLineGrid",
        "features.transactions.grids.TransactionLineModel",
        "ui.table_keyboard_policy.StandardTableKeyboardMixin",
        "sales_invoice document route",
    ),
    "requirements": (
        "Editors opened by AnyKeyPressed, double click or programmatic focus must install the standard Enter event filter.",
        "Sales invoice Enter route is semantic: item -> unit -> qty -> price -> discount -> tax -> total -> notes.",
        "TransactionLineModel owns row lifecycle and exposes ensure_single_trailing_empty_line().",
        "add_empty_line() is idempotent and reuses an existing trailing blank row.",
        "Table keyboard policy delegates trailing-row creation to the model lifecycle gate when available.",
        "The phase must stay PyQt-free-testable through unified_grid_navigation_policy.py.",
    ),
    "required_files": (
        "PHASE415_UNIFIED_SALES_INVOICE_GRID_RUNTIME.md",
        "alrajhi_client/features/transactions/grids/unified_grid_navigation_policy.py",
        "alrajhi_client/workspace/quality/unified_sales_invoice_grid_runtime_contract.py",
        "tools/phase415_unified_sales_invoice_grid_runtime_guard.py",
        "tests/test_phase415_unified_sales_invoice_grid_runtime.py",
    ),
    "required_outputs": (
        "tools/audit_outputs/unified_sales_invoice_grid_runtime_matrix.csv",
    ),
}


def unified_sales_invoice_grid_runtime_summary(root: Path | None = None) -> dict[str, object]:
    base = root or ROOT
    missing = [path for path in UNIFIED_SALES_INVOICE_GRID_RUNTIME_CONTRACT["required_files"] if not (base / path).exists()]
    return {
        "phase": 415,
        "name": "unified_sales_invoice_grid_runtime",
        "ready": not missing,
        "missing": missing,
    }
