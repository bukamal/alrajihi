# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase389_custom_and_smart_tables_are_row_action_by_default():
    custom = read("alrajhi_client/views/custom_table_view.py")
    smart = read("alrajhi_client/ui/smart_table_view.py")
    assert "Phase389" in custom
    assert "self.init_standard_table_keyboard()" not in custom
    assert "not getattr(self, \"_standard_keyboard_active\", False)" in smart
    assert "self.setSelectionBehavior(self.SelectRows)" in smart
    assert "self.setSelectionMode(self.ExtendedSelection)" in smart


def test_phase389_selected_source_rows_falls_back_from_cell_selection():
    smart = read("alrajhi_client/ui/smart_table_view.py")
    assert "def selected_source_rows" in smart
    assert "selectedRows()" in smart
    assert "selectedIndexes()" in smart
    assert "currentIndex()" in smart
    assert "seen = set()" in smart


def test_phase389_only_editable_grids_enable_enter_cell_traversal():
    custom = read("alrajhi_client/views/custom_table_view.py")
    transaction_grid = read("alrajhi_client/features/transactions/grids/transaction_line_grid.py")
    editable_grid = read("alrajhi_client/ui/editable_smart_grid.py")
    runtime = read("alrajhi_client/ui/runtime_visual_polish.py")
    assert "self.init_standard_table_keyboard()" not in custom
    assert "self.init_standard_table_keyboard()" in transaction_grid
    assert "self.setSelectionBehavior(self.SelectItems)" in transaction_grid
    assert "self.init_standard_table_keyboard()" in editable_grid
    assert "standard_table_keyboard" in runtime
    assert "QAbstractItemView.SelectItems" in runtime
    assert "QAbstractItemView.SelectRows" in runtime


def test_phase389_guard_contract_ready():
    from workspace.quality.editable_grid_row_action_boundary_contract import editable_grid_row_action_boundary_summary

    summary = editable_grid_row_action_boundary_summary(ROOT)
    assert summary["ready"], summary
    assert summary["checks"] >= 8


def test_phase389_release_gate_registered_and_documented():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "editable_grid_row_action_boundary" in gate
    assert "tools/phase389_editable_grid_row_action_boundary_guard.py" in gate
    assert '(389, "editable_grid_row_action_boundary")' in gate
    assert (ROOT / "PHASE389_EDITABLE_GRID_ROW_ACTION_BOUNDARY.md").exists()
