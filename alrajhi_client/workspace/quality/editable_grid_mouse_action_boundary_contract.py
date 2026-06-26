# -*- coding: utf-8 -*-
"""Phase 388 contract: editable grid Enter routing must not steal mouse action clicks."""
from __future__ import annotations

EDITABLE_GRID_MOUSE_ACTION_BOUNDARY_PHASE = 388

REQUIRED_GUARANTEES = (
    "enter_commit_sets_explicit_navigation_intent",
    "editor_close_without_enter_does_not_advance_grid_cell",
    "mouse_focus_out_to_side_buttons_preserves_button_click",
    "edit_next_previous_hints_remain_keyboard_navigation",
)


def contract_summary() -> dict[str, object]:
    return {
        "phase": EDITABLE_GRID_MOUSE_ACTION_BOUNDARY_PHASE,
        "scope": "editable_table_keyboard_policy",
        "guarantees": REQUIRED_GUARANTEES,
        "reason": "Side action buttons such as edit/delete/print must remain clickable while an editable grid cell editor is active.",
    }
