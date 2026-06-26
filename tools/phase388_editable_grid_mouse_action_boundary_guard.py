#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 388 guard: mouse clicks on side actions are not consumed by grid Enter routing."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "tools" / "audit_outputs" / "editable_grid_mouse_action_boundary_matrix.csv"
CHECKS: list[dict[str, object]] = []


def add_check(name: str, ok: bool, detail: str) -> None:
    CHECKS.append({"check": name, "ok": bool(ok), "detail": detail})


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def main() -> int:
    keyboard = read("alrajhi_client/ui/table_keyboard_policy.py")
    quality = read("alrajhi_client/workspace/quality/editable_grid_mouse_action_boundary_contract.py")

    add_check(
        "explicit enter navigation flag",
        "_standard_editor_close_navigation" in keyboard and '"next"' in keyboard and '"previous"' in keyboard,
        "Enter/Shift+Enter mark the intended editor-close navigation direction explicitly",
    )
    add_check(
        "enter event sets pending before close",
        'self._standard_editor_close_navigation = "next"' in keyboard and 'self._standard_editor_close_navigation = "previous"' in keyboard,
        "the editor eventFilter sets pending navigation only for keyboard Enter commits",
    )
    add_check(
        "close editor helper exists",
        "def _standard_editor_close_should_navigate(self, hint)" in keyboard,
        "closeEditor delegates navigation decisions to a helper",
    )
    add_check(
        "nohint is not auto navigation",
        "NoHint/SubmitModelCache may be focus-out, mouse click, model reset" in keyboard and "return None" in keyboard,
        "NoHint focus loss from mouse clicks does not advance to another grid cell",
    )
    add_check(
        "close editor consumes pending and skips none",
        "direction = self._standard_editor_close_should_navigate(hint)" in keyboard and "self._standard_editor_close_navigation = None" in keyboard and "or direction is None" in keyboard,
        "closeEditor clears the pending flag and exits when no keyboard navigation was requested",
    )
    add_check(
        "keyboard next previous hints preserved",
        "if hint == QAbstractItemDelegate.EditPreviousItem:" in keyboard and "if hint == QAbstractItemDelegate.EditNextItem:" in keyboard,
        "real delegate keyboard hints still move between cells",
    )
    add_check(
        "phase388 documented in docstring",
        "Phase388 prevents mouse-triggered focus loss" in keyboard and "edit/delete/print" in keyboard,
        "keyboard policy documents the mouse-action boundary",
    )
    add_check(
        "quality contract",
        "EDITABLE_GRID_MOUSE_ACTION_BOUNDARY_PHASE = 388" in quality and "mouse_focus_out_to_side_buttons_preserves_button_click" in quality,
        "quality contract records the Phase 388 guarantee",
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "ok", "detail"])
        writer.writeheader()
        writer.writerows(CHECKS)

    failed = [row for row in CHECKS if not row["ok"]]
    if failed:
        print(f"Phase 388 editable grid mouse-action boundary guard FAILED: {len(failed)} issue(s)")
        for row in failed:
            print(f"- {row['check']}: {row['detail']}")
        return 1
    print(f"Phase 388 editable grid mouse-action boundary guard passed: {len(CHECKS)} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
