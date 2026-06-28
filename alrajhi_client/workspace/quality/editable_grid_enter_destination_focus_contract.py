# -*- coding: utf-8 -*-
"""Contract for Phase426 editable-grid Enter destination focus hotfix.

Phase425 prevented committing an untouched *source* editor.  The remaining
runtime symptom was different: Enter moved to the next cell and auto-opened its
editor, so the destination delegate could serialize an empty/default editor
state and clear the cell that focus had just reached.

This contract is Qt-free and protects the corrected rule: Enter navigation moves
selection/focus only; editors open from actual edit triggers such as typing,
F2/double-click, or explicit document focus helpers.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

PHASE426_EDITABLE_GRID_ENTER_DESTINATION_FOCUS = {
    "phase": 426,
    "name": "editable_grid_enter_destination_focus_hotfix",
    "problem": "Enter preserved the source editor but could still clear the destination cell by auto-opening and closing its delegate editor.",
    "owner": "alrajhi_client.ui.table_keyboard_policy.StandardTableKeyboardMixin",
    "requirements": (
        "Enter on a focused non-editing cell navigates without opening the editor.",
        "Enter after closing an active editor focuses the next/previous cell with start_edit=False.",
        "Destination cells are selected for visibility but not auto-edited by Enter navigation.",
        "Typing and explicit edit triggers still open editors through Qt's normal edit triggers.",
    ),
}


def _read(root: Path, rel: str) -> str:
    path = root / rel
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _handle_enter_block(text: str) -> str:
    start = text.find("def _standard_handle_enter_key")
    end = text.find("\n    def currentChanged", start)
    if start < 0:
        return ""
    return text[start:end if end > start else len(text)]


def _close_editor_block(text: str) -> str:
    start = text.find("def closeEditor")
    end = text.find("\n\n", start)
    if start < 0:
        return ""
    # include the full method body until EOF if simple paragraph slicing fails
    next_def = text.find("\n    def ", start + 1)
    return text[start:next_def if next_def > start else len(text)]


def editable_grid_enter_destination_focus_summary(root: Path | str) -> Dict[str, object]:
    base = Path(root)
    keyboard = _read(base, "alrajhi_client/ui/table_keyboard_policy.py")
    handle = _handle_enter_block(keyboard)
    close = _close_editor_block(keyboard)
    markers = {
        "phase426_docstring": "Phase426 makes Enter movement focus-only" in keyboard,
        "non_editing_enter_focus_only": "Enter on a focused, non-editing cell is navigation only" in handle,
        "non_editing_enter_no_edit_current": "self.edit(current)" not in handle,
        "non_editing_enter_next_focus_only": "self._standard_focus_index(next_index, start_edit=False)" in handle,
        "shift_enter_focus_only": "forward=False), start_edit=False" in handle,
        "close_next_focus_only": "self._standard_focus_index(target, start_edit=False)" in close,
        "close_fallback_focus_only": "self._standard_focus_index(self._standard_next_index(idx, True), start_edit=False)" in close,
        "close_previous_focus_only": "self._standard_focus_index(self._standard_next_index(idx, False), start_edit=False)" in close,
        "typing_still_opens_editor": "QAbstractItemView.AnyKeyPressed" in keyboard,
        "gated_commit_preserved": "self._standard_commit_enter_editor_if_modified(obj)" in keyboard,
    }
    return {
        "phase": 426,
        "ready": all(markers.values()),
        "markers": markers,
        "failures": [key for key, ok in markers.items() if not ok],
    }


def editable_grid_enter_destination_focus_matrix(root: Path | str) -> List[Dict[str, str]]:
    summary = editable_grid_enter_destination_focus_summary(root)
    return [
        {
            "key": key,
            "category": "enter_destination_focus",
            "path": "alrajhi_client/ui/table_keyboard_policy.py",
            "status": "OK" if ok else "FAIL",
            "detail": "Phase426 focus-only Enter marker present" if ok else "missing Phase426 marker",
        }
        for key, ok in summary["markers"].items()
    ]


__all__ = [
    "PHASE426_EDITABLE_GRID_ENTER_DESTINATION_FOCUS",
    "editable_grid_enter_destination_focus_summary",
    "editable_grid_enter_destination_focus_matrix",
]
