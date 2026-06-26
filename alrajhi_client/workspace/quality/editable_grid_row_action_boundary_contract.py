# -*- coding: utf-8 -*-
"""Phase 389 contract: editable grid keyboard policy must not break row actions.

The project has two different table interaction modes:

* editable line-entry grids: current-cell selection + Enter traversal.
* list/action tables: full-row selection so Edit/Delete/Print actions can resolve
  the selected business row.

This contract keeps those modes separated after the global keyboard/visual polish
passes.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Phase389Check:
    key: str
    category: str
    description: str
    path: str
    status: bool
    detail: str = ""

    def to_row(self) -> Dict[str, object]:
        return asdict(self)


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def _exists(path: str, root: Path | None = None) -> bool:
    return ((root or ROOT) / path).exists()


def editable_grid_row_action_boundary_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    files = {
        "custom": "alrajhi_client/views/custom_table_view.py",
        "smart": "alrajhi_client/ui/smart_table_view.py",
        "runtime": "alrajhi_client/ui/runtime_visual_polish.py",
        "keyboard": "alrajhi_client/ui/table_keyboard_policy.py",
        "transaction_grid": "alrajhi_client/features/transactions/grids/transaction_line_grid.py",
        "editable_grid": "alrajhi_client/ui/editable_smart_grid.py",
        "invoices": "alrajhi_client/views/widgets/invoices_widget.py",
        "returns": "alrajhi_client/views/widgets/returns_widget.py",
    }
    source = {name: _read(path, base) if _exists(path, base) else "" for name, path in files.items()}
    checks: List[Phase389Check] = []

    checks.append(Phase389Check(
        "custom_table_does_not_auto_enable_entry_keyboard",
        "selection",
        "CustomTableView stays a row-action/list table by default instead of forcing cell selection",
        files["custom"],
        "Phase389" in source["custom"] and "self.init_standard_table_keyboard()" not in source["custom"],
        "CustomTableView must not auto-call init_standard_table_keyboard",
    ))
    checks.append(Phase389Check(
        "smart_table_row_action_defaults",
        "selection",
        "SmartTableView restores SelectRows/ExtendedSelection when the editable keyboard policy is not active",
        files["smart"],
        "Phase389" in source["smart"] and "self.setSelectionBehavior(self.SelectRows)" in source["smart"] and "not getattr(self, \"_standard_keyboard_active\", False)" in source["smart"],
        "SmartTableView.apply_enterprise_defaults must protect list table row selection",
    ))
    checks.append(Phase389Check(
        "selected_source_rows_cell_fallback",
        "actions",
        "Row action helpers recover a business row from selected cells/current cell if an old state selected only a cell",
        files["smart"],
        "selectedIndexes" in source["smart"] and "currentIndex" in source["smart"] and "seen = set()" in source["smart"],
        "selected_source_rows must tolerate selectedIndexes/currentIndex fallback",
    ))
    checks.append(Phase389Check(
        "transaction_grid_explicit_entry_keyboard",
        "editable-grid",
        "TransactionLineGrid explicitly opts into the Enter navigation policy",
        files["transaction_grid"],
        "self.init_standard_table_keyboard()" in source["transaction_grid"] and "self.setSelectionBehavior(self.SelectItems)" in source["transaction_grid"],
        "TransactionLineGrid must keep current-cell selection and Enter traversal",
    ))
    checks.append(Phase389Check(
        "editable_smart_grid_keeps_entry_keyboard",
        "editable-grid",
        "EditableSmartGrid remains an editable entry grid with standard Enter traversal",
        files["editable_grid"],
        "class EditableSmartGrid(StandardTableKeyboardMixin" in source["editable_grid"] and "self.init_standard_table_keyboard()" in source["editable_grid"],
        "EditableSmartGrid must keep explicit keyboard policy",
    ))
    checks.append(Phase389Check(
        "runtime_polish_respects_mode_boundary",
        "runtime",
        "Runtime visual polish chooses SelectItems only for standard editable keyboard tables and SelectRows otherwise",
        files["runtime"],
        "standard_table_keyboard" in source["runtime"] and "QAbstractItemView.SelectItems" in source["runtime"] and "QAbstractItemView.SelectRows" in source["runtime"],
        "Runtime table polish must preserve list vs editable selection modes",
    ))
    checks.append(Phase389Check(
        "invoice_lists_request_rows",
        "actions",
        "Sales and purchase invoice lists request row selection for Edit/Delete/Print actions",
        files["invoices"],
        "sales_table.setSelectionBehavior(SmartTableView.SelectRows)" in source["invoices"] and "purchases_table.setSelectionBehavior(SmartTableView.SelectRows)" in source["invoices"] and "selected_source_rows" in source["invoices"],
        "Invoice lists must resolve actions from selected source rows",
    ))
    checks.append(Phase389Check(
        "return_lists_request_rows",
        "actions",
        "Sales/purchase return lists request row selection and use selected source rows for actions",
        files["returns"],
        "setSelectionBehavior(SmartTableView.SelectRows)" in source["returns"] and "selected_source_rows" in source["returns"] and "selectionChanged.connect" in source["returns"],
        "Return lists must resolve actions from selected source rows",
    ))
    return [c.to_row() for c in checks]


def editable_grid_row_action_boundary_summary(root: Path | None = None) -> Dict[str, object]:
    rows = editable_grid_row_action_boundary_matrix(root)
    failed = [row for row in rows if not row["status"]]
    return {
        "phase": 389,
        "checks": len(rows),
        "failures": len(failed),
        "ready": not failed,
        "failed_keys": [str(row["key"]) for row in failed],
    }


__all__ = [
    "editable_grid_row_action_boundary_matrix",
    "editable_grid_row_action_boundary_summary",
]
