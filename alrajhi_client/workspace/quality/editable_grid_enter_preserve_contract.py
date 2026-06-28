# -*- coding: utf-8 -*-
"""Contract for Phase425 editable-grid Enter preserve hotfix.

This module is Qt-free by design.  It validates that the shared keyboard policy
no longer commits an untouched editor when Enter is used only for navigation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

PHASE425_EDITABLE_GRID_ENTER_PRESERVE = {
    "phase": 425,
    "name": "editable_grid_enter_preserve_hotfix",
    "problem": "Enter inside an already-open cell editor can clear cell data when an untouched delegate commits an empty editor state.",
    "owner": "alrajhi_client.ui.table_keyboard_policy.StandardTableKeyboardMixin",
    "requirements": (
        "Track whether the operator actually modified the active editor.",
        "Do not call commitData() for untouched editors during Enter/Shift+Enter navigation.",
        "Close untouched editors for navigation without writing blank values into the model.",
        "Preserve the existing Phase388 mouse-focus boundary and Phase412 centralized navigation engine.",
    ),
    "runtime_expectation": "Opening a cell and pressing Enter must preserve the original model value and move focus to the semantic next cell.",
}


def _read(root: Path, rel: str) -> str:
    path = root / rel
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def editable_grid_enter_preserve_summary(root: Path | str) -> Dict[str, object]:
    base = Path(root)
    keyboard = _read(base, "alrajhi_client/ui/table_keyboard_policy.py")
    markers = {
        "dirty_tracking": "def _standard_install_editor_dirty_tracking" in keyboard,
        "user_modified_flag": "standard_enter_user_modified" in keyboard,
        "initial_snapshot": "standard_enter_initial_text" in keyboard,
        "gated_commit_helper": "def _standard_commit_enter_editor_if_modified" in keyboard,
        "enter_uses_gated_commit": "self._standard_commit_enter_editor_if_modified(obj)" in keyboard,
        "direct_enter_commit_removed": "self.commitData(obj)" not in keyboard.replace("``self.commitData(obj)``", ""),
        "nohint_navigation_kept": "self.closeEditor(obj, QAbstractItemDelegate.NoHint)" in keyboard,
        "shift_enter_navigation_kept": "self.closeEditor(obj, QAbstractItemDelegate.EditPreviousItem)" in keyboard,
    }
    return {
        "phase": 425,
        "ready": all(markers.values()),
        "markers": markers,
        "failures": [key for key, ok in markers.items() if not ok],
    }


def editable_grid_enter_preserve_matrix(root: Path | str) -> List[Dict[str, str]]:
    summary = editable_grid_enter_preserve_summary(root)
    markers = summary["markers"]
    return [
        {
            "key": key,
            "category": "enter_preserve",
            "path": "alrajhi_client/ui/table_keyboard_policy.py",
            "status": "OK" if ok else "FAIL",
            "detail": "required Phase425 marker present" if ok else "missing Phase425 marker",
        }
        for key, ok in markers.items()
    ]


__all__ = [
    "PHASE425_EDITABLE_GRID_ENTER_PRESERVE",
    "editable_grid_enter_preserve_summary",
    "editable_grid_enter_preserve_matrix",
]
