# -*- coding: utf-8 -*-
"""Phase411 Basit shell menu rebuild and paint hotfix contract.

This import-safe contract protects the main IconMenuBar from the fixed
left-corner artefact that could remain after RTL/LTR language rebuilds or from
native QToolButton menu sub-controls.
"""
from __future__ import annotations

BASIT_SHELL_MENU_REBUILD_CONTRACT = {
    "phase": 411,
    "name": "basit_shell_menu_rebuild_hotfix",
    "scope": "main_window.IconMenuBar",
    "symptom": "A stale/native popup paint artefact appears at the upper-left corner of the menu bar while real menu icons may move with language direction.",
    "requirements": (
        "IconMenuBar owns a styled background so the shell repaints its full surface.",
        "Vertical margins are derived from shell metrics and do not exceed available navigation height.",
        "Menu buttons do not attach QMenu directly with setMenu/InstantPopup.",
        "Menus are opened manually at the clicked button position.",
        "Native QToolButton menu sub-controls are explicitly suppressed in inline and global QSS.",
        "After language/menu rebuild, layout invalidation and repaint are requested.",
    ),
    "required_outputs": (
        "tools/audit_outputs/basit_shell_menu_rebuild_matrix.csv",
    ),
    "acceptance_rule": (
        "The left-corner artefact is treated as a shell rebuild/paint defect, not as a dashboard or language-direction defect. "
        "The guard must confirm that stale menu widgets and native popup sub-controls cannot persist at x=0."
    ),
}


def required_outputs() -> tuple[str, ...]:
    return tuple(BASIT_SHELL_MENU_REBUILD_CONTRACT["required_outputs"])
