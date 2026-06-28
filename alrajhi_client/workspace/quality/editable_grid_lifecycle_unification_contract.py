# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

EDITABLE_GRID_LIFECYCLE_UNIFICATION_CONTRACT = {
    "phase": 418,
    "name": "editable_grid_lifecycle_unification",
    "scope": (
        "features.transactions.grids.TransactionLineModel",
        "features.inventory.grids.InventoryTransferLinesModel",
        "features.manufacturing.grids.BomComponentsModel",
        "ui.table_keyboard_policy.StandardTableKeyboardMixin",
        "features.transactions.grids.unified_grid_navigation_policy",
    ),
    "requirements": (
        "Every model-backed editable operational grid exposes ensure_single_trailing_empty_line().",
        "add_empty_line() must be idempotent and delegate to ensure_single_trailing_empty_line().",
        "Duplicate trailing blank rows must be trimmed through trim_extra_trailing_empty_lines().",
        "Inventory transfer and BOM add-item paths must reuse an existing trailing blank row.",
        "Business Enter routes include invoice, return, inventory transfer, BOM and material-unit routes.",
        "Material unit rows remain explicitly user-created and must not auto-append on Enter.",
    ),
    "required_files": (
        "PHASE418_EDITABLE_GRID_LIFECYCLE_UNIFICATION.md",
        "alrajhi_client/workspace/quality/editable_grid_lifecycle_unification_contract.py",
        "tools/phase418_editable_grid_lifecycle_unification_guard.py",
        "tests/test_phase418_editable_grid_lifecycle_unification.py",
    ),
    "required_outputs": (
        "tools/audit_outputs/editable_grid_lifecycle_unification_matrix.csv",
    ),
}


def editable_grid_lifecycle_unification_summary(root: Path | None = None) -> dict[str, object]:
    base = root or ROOT
    missing = [path for path in EDITABLE_GRID_LIFECYCLE_UNIFICATION_CONTRACT["required_files"] if not (base / path).exists()]
    return {
        "phase": 418,
        "name": "editable_grid_lifecycle_unification",
        "ready": not missing,
        "missing": missing,
    }


__all__ = [
    "EDITABLE_GRID_LIFECYCLE_UNIFICATION_CONTRACT",
    "editable_grid_lifecycle_unification_summary",
]
