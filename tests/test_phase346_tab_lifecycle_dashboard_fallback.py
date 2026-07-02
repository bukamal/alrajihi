# -*- coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.shell.tab_lifecycle_contract import (
    tab_lifecycle_checks,
    tab_lifecycle_issues,
    tab_lifecycle_summary,
)


def test_phase346_dashboard_is_fixed_surface_not_tab():
    main = (ROOT / "alrajhi_client/views/main_window.py").read_text(encoding="utf-8")
    workspace = (ROOT / "alrajhi_client/shell/tab_workspace.py").read_text(encoding="utf-8")
    assert "self.workspace_host" in main
    assert "_install_fixed_dashboard_surface" in main
    assert "if pid == 'dashboard':" in main
    assert "_show_fixed_dashboard" in main
    assert "FIXED_SURFACE_TAB_IDS" in workspace
    assert '"dashboard"' in workspace


def test_phase346_tab_close_has_dashboard_fallback_no_white_surface():
    workspace = (ROOT / "alrajhi_client/shell/tab_workspace.py").read_text(encoding="utf-8")
    main = (ROOT / "alrajhi_client/views/main_window.py").read_text(encoding="utf-8")
    assert "emptyWorkspace = pyqtSignal()" in workspace
    assert "self.emptyWorkspace.emit()" in workspace
    assert "next_index" in workspace
    assert "emptyWorkspace.connect" in main
    assert "_show_fixed_dashboard(refresh=False)" in main


def test_phase346_save_buttons_are_shell_managed_no_direct_accept():
    dialog_tab = (ROOT / "alrajhi_client/features/dialog_documents/dialog_document_tab.py").read_text(encoding="utf-8")
    returns = (ROOT / "alrajhi_client/features/returns/return_editor_tabs.py").read_text(encoding="utf-8")
    actions = (ROOT / "alrajhi_client/features/returns/components/return_actions.py").read_text(encoding="utf-8")
    main = (ROOT / "alrajhi_client/views/main_window.py").read_text(encoding="utf-8")
    assert "save_without_closing" in dialog_tab
    workspace_save_body = dialog_tab.split("def workspace_save", 1)[1].split("def workspace_print", 1)[0]
    assert "'accept'" not in workspace_save_body
    assert "QTimer.singleShot(0" in main
    assert "_close_saved_document_tab" in main
    assert "close_tab_at(index)" in main
    assert "_save_return_document(close_after_save=False)" in returns
    assert "_save_return_document(close_after_save=True)" in returns
    assert "_save_return_document(close_after_save=False)" in actions


def test_phase346_contract_guard_has_no_issues():
    rows = tab_lifecycle_checks(ROOT)
    assert len(rows) >= 14
    assert tab_lifecycle_issues(ROOT) == {}
    summary = tab_lifecycle_summary(ROOT)
    assert summary["phase"] == 346
    assert summary["issue_groups"] == 0
    assert summary["ready"] is True


def test_phase346_release_registration_exists():
    release_gate = (ROOT / "alrajhi_client/workspace/quality/release_gate_contract.py").read_text(encoding="utf-8")
    assert "tab_lifecycle_dashboard_fallback" in release_gate
    assert "TAB_LIFECYCLE_DASHBOARD_FALLBACK" in release_gate
