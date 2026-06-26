# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase337_shared_keyboard_policy_exists_and_defines_enter_contract():
    policy = read("alrajhi_client/ui/table_keyboard_policy.py")
    assert "class StandardTableKeyboardMixin" in policy
    assert "def init_standard_table_keyboard" in policy
    assert "def _standard_handle_enter_key" in policy
    assert "Qt.Key_Return" in policy and "Qt.Key_Enter" in policy
    assert "Qt.ShiftModifier" in policy
    assert "add_empty_line" in policy
    assert "EditNextItem" in policy and "EditPreviousItem" in policy
    assert "Esc is not consumed" in policy


def test_phase337_editable_table_classes_install_standard_keyboard_policy():
    custom = read("alrajhi_client/views/custom_table_view.py")
    editable = read("alrajhi_client/ui/editable_smart_grid.py")
    transaction_grid = read("alrajhi_client/features/transactions/grids/transaction_line_grid.py")
    assert "from ui.table_keyboard_policy import StandardTableKeyboardMixin" in custom
    assert "class CustomTableView(StandardTableKeyboardMixin, QTableView):" in custom
    assert "self.init_standard_table_keyboard()" not in custom
    assert "from ui.table_keyboard_policy import StandardTableKeyboardMixin" in editable
    assert "class EditableSmartGrid(StandardTableKeyboardMixin, QTableWidget):" in editable
    assert "self.init_standard_table_keyboard()" in editable
    assert "self.init_standard_table_keyboard()" in transaction_grid


def test_phase337_policy_is_model_view_only_and_keeps_dashboard_escape_global():
    policy = read("alrajhi_client/ui/table_keyboard_policy.py")
    forbidden_imports = ["from database", "import database", "repository import", "gateway import", "printing_service", "settings_service"]
    lowered = policy.lower()
    for word in forbidden_imports:
        assert word not in lowered
    assert "level Esc-to-dashboard shortcut remains in control" in policy


def test_phase337_release_gate_registered_and_documented():
    gate = read("tools/audit_outputs/release_readiness_gate_matrix.csv")
    assert "editable_table_keyboard_standard" in gate
    assert "tests/test_phase337_editable_table_keyboard_standard.py" in gate
    assert (ROOT / "PHASE337_EDITABLE_TABLE_KEYBOARD_STANDARD.md").exists()
