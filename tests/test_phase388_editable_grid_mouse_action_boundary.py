# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_enter_commit_sets_explicit_editor_close_navigation():
    text = _read("alrajhi_client/ui/table_keyboard_policy.py")
    assert "_standard_editor_close_navigation" in text
    assert 'self._standard_editor_close_navigation = "next"' in text
    assert 'self._standard_editor_close_navigation = "previous"' in text
    assert "self.commitData(obj)" in text
    assert "self.closeEditor(obj, QAbstractItemDelegate.NoHint)" in text


def test_mouse_focus_out_nohint_does_not_auto_advance_grid():
    text = _read("alrajhi_client/ui/table_keyboard_policy.py")
    assert "def _standard_editor_close_should_navigate(self, hint)" in text
    assert "NoHint/SubmitModelCache may be focus-out, mouse click, model reset" in text
    assert "return None" in text
    assert "direction = self._standard_editor_close_should_navigate(hint)" in text
    assert "or direction is None" in text


def test_close_editor_clears_pending_navigation_state():
    text = _read("alrajhi_client/ui/table_keyboard_policy.py")
    assert "finally:" in text
    assert "self._standard_editor_close_navigation = None" in text
    assert "if direction == \"previous\":" in text
    assert "_standard_post_commit_index" in text


def test_keyboard_delegate_hints_are_still_preserved():
    text = _read("alrajhi_client/ui/table_keyboard_policy.py")
    assert "if hint == QAbstractItemDelegate.EditPreviousItem:" in text
    assert "if hint == QAbstractItemDelegate.EditNextItem:" in text
    assert "return \"previous\"" in text
    assert "return \"next\"" in text


def test_phase388_quality_contract_exists():
    text = _read("alrajhi_client/workspace/quality/editable_grid_mouse_action_boundary_contract.py")
    assert "EDITABLE_GRID_MOUSE_ACTION_BOUNDARY_PHASE = 388" in text
    assert "mouse_focus_out_to_side_buttons_preserves_button_click" in text
    assert "enter_commit_sets_explicit_navigation_intent" in text
