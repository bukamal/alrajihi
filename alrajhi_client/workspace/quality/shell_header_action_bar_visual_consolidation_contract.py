# -*- coding: utf-8 -*-
"""Phase446 shell header and global action-bar visual consolidation contract.

The shell is visible on every workspace.  This Qt-free contract verifies that
main navigation and the global action bar use the project identity tokens and
semantic roles instead of the older heavy Basit-like blue/red/yellow chrome.
"""
from __future__ import annotations
from pathlib import Path

REQUIRED_BRAND_TOKENS = [
    "shell_visual_identity_phase",
    "shell_navigation_bg",
    "shell_navigation_button_bg",
    "shell_navigation_button_text",
    "shell_navigation_button_hover_bg",
    "shell_action_bar_bg",
    "shell_action_primary_bg_phase446",
    "shell_action_secondary_bg_phase446",
    "shell_action_compact_min_width",
]

REQUIRED_MAIN_WINDOW_MARKERS = [
    "Phase446: calm, centralized shell navigation chrome.",
    "visualRole', 'shell_navigation'",
    "visualRole', 'shell_nav_button'",
    "projectVisualIdentityPhase', 446",
    "shell_navigation_button_bg",
    "shell_navigation_home_bg",
]

REQUIRED_ACTION_BAR_MARKERS = [
    "BRANDED_ACTION_BAR_PHASE = 446",
    "visualRole', 'shell_action_bar'",
    "visualRole', 'shell_action_button'",
    "visualRole', 'shell_action_utility'",
    "Phase446: global action bar is secondary shell chrome",
    "shell_action_primary_bg_phase446",
    "shell_action_secondary_bg_phase446",
]

REQUIRED_QSS_MARKERS = [
    'QFrame#CleanShellNavigationBar[projectVisualIdentityPhase="446"]',
    'QPushButton#MainNavButton[projectVisualIdentityPhase="446"]',
    'QFrame#UnifiedActionBar[projectVisualIdentityPhase="446"]',
    'project-wide shell header and action bar consolidation',
]

FORBIDDEN_NAV_SNIPPETS = [
    "/* Phase406: Basit-inspired shell navigation chrome. */",
    "background: {basit_blue};",
    "border-bottom: 2px solid",
]

FORBIDDEN_ACTION_SNIPPETS = [
    "/* Phase406: Basit-inspired shared action bar runtime. */",
    "background: {basit_red};",
    "border-radius: 3px;\n                padding: 7px 11px;",
]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def phase446_shell_header_action_bar_visual_consolidation_summary(root: str | Path) -> dict:
    root = Path(root)
    details: list[str] = []
    checks = 0

    brand = _read(root, "alrajhi_client/theme/brand.py")
    for token in REQUIRED_BRAND_TOKENS:
        checks += 1
        if token not in brand:
            details.append(f"missing Phase446 brand token: {token}")
    checks += 1
    if not any(marker in brand for marker in ("'project_visual_identity_phase': 446", "'project_visual_identity_phase': 447", "'project_visual_identity_phase': 450", "'project_visual_identity_phase': 451")):
        details.append("project_visual_identity_phase must be 446 or later")
    checks += 1
    if not any(marker in brand for marker in ("'legacy_visual_style_sweep_phase': 446", "'legacy_visual_style_sweep_phase': 447", "'legacy_visual_style_sweep_phase': 450", "'legacy_visual_style_sweep_phase': 451")):
        details.append("legacy_visual_style_sweep_phase must be 446 or later")

    main_window = _read(root, "alrajhi_client/views/main_window.py")
    for marker in REQUIRED_MAIN_WINDOW_MARKERS:
        checks += 1
        if marker not in main_window:
            details.append(f"main shell navigation missing marker: {marker}")
    for marker in FORBIDDEN_NAV_SNIPPETS:
        checks += 1
        if marker in main_window:
            details.append(f"main shell navigation still contains heavy legacy chrome: {marker}")

    action_bar = _read(root, "alrajhi_client/shell/unified_action_bar.py")
    for marker in REQUIRED_ACTION_BAR_MARKERS:
        checks += 1
        if marker not in action_bar:
            details.append(f"action bar missing marker: {marker}")
    for marker in FORBIDDEN_ACTION_SNIPPETS:
        checks += 1
        if marker in action_bar:
            details.append(f"action bar still contains heavy legacy chrome: {marker}")

    qss = _read(root, "alrajhi_client/theme/qss.py")
    for marker in REQUIRED_QSS_MARKERS:
        checks += 1
        if marker not in qss:
            details.append(f"central QSS missing Phase446 shell marker: {marker}")

    return {
        "ready": not details,
        "issues": len(details),
        "checks": checks,
        "details": details,
        "phase": 446,
    }


__all__ = ["phase446_shell_header_action_bar_visual_consolidation_summary"]
