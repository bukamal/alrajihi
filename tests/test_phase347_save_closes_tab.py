# -*- coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.shell.save_close_after_save_contract import (
    save_close_checks,
    save_close_issues,
    save_close_summary,
)


def _body(source: str, name: str) -> str:
    marker = f"    def {name}"
    start = source.find(marker)
    assert start >= 0, name
    nxt = source.find("\n    def ", start + len(marker))
    return source[start:] if nxt < 0 else source[start:nxt]


def test_phase347_successful_save_closes_tab_via_saved_signal_policy():
    main = (ROOT / "alrajhi_client/views/main_window.py").read_text(encoding="utf-8")
    open_doc = _body(main, "_open_document_tab")
    on_saved = _body(main, "_on_document_saved")
    close_saved = _body(main, "_close_saved_document_tab")
    assert "widget.saved.connect(lambda *_args: self._on_document_saved(widget))" in open_doc
    assert "QTimer.singleShot(0" in on_saved
    assert "_close_saved_document_tab" in on_saved
    assert "close_tab_at(index)" in close_saved
    assert "mark_dirty(tab_id, False)" in close_saved
    assert "removeTab" not in close_saved


def test_phase347_dashboard_remains_fixed_not_tab():
    main = (ROOT / "alrajhi_client/views/main_window.py").read_text(encoding="utf-8")
    workspace = (ROOT / "alrajhi_client/shell/tab_workspace.py").read_text(encoding="utf-8")
    assert "_install_fixed_dashboard_surface" in main
    assert "fixedDashboardSurface" in main
    assert "dashboard.setWindowTitle('')" in main
    assert "FIXED_SURFACE_TAB_IDS" in workspace
    assert '"dashboard"' in workspace
    assert "return -1" in workspace


def test_phase347_global_save_invokes_save_only_close_is_saved_driven():
    main = (ROOT / "alrajhi_client/views/main_window.py").read_text(encoding="utf-8")
    save_current = _body(main, "save_current_tab")
    assert "_invoke_current_tab_command" in save_current
    assert "close_tab_at" not in save_current
    assert "removeTab" not in save_current
    assert "_should_close_tab_after_save" in main
    assert "prevent_close_after_save" in main
    assert "stay_open_after_save" in main


def test_phase347_contract_guard_has_no_issues():
    rows = save_close_checks(ROOT)
    assert len(rows) >= 10
    assert save_close_issues(ROOT) == {}
    summary = save_close_summary(ROOT)
    assert summary["phase"] == 347
    assert summary["issue_groups"] == 0
    assert summary["ready"] is True


def test_phase347_release_registration_exists():
    release_gate = (ROOT / "alrajhi_client/workspace/quality/release_gate_contract.py").read_text(encoding="utf-8")
    assert "save_closes_tab" in release_gate
    assert "SAVE_CLOSES_TAB" in release_gate
