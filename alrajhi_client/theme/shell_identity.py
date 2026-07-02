# -*- coding: utf-8 -*-
"""Phase 354: branded shell chrome contract.

PyQt-free description of the visual identity expected from workspace tabs,
main navigation menus and the global action bar.  The runtime widgets consume
these names and tokens so future shell changes remain centralized.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence

SHELL_IDENTITY_PHASE = 354


@dataclass(frozen=True)
class ShellTokenSpec:
    key: str
    role: str
    description: str


REQUIRED_SHELL_TOKEN_SPECS: Sequence[ShellTokenSpec] = (
    ShellTokenSpec("shell_tab_main_badge_bg", "tab", "Badge surface for main workspace tabs."),
    ShellTokenSpec("shell_tab_sub_badge_bg", "tab", "Badge surface for document/sub-workspace tabs."),
    ShellTokenSpec("shell_tab_badge_text", "tab", "Readable text color for tab type badges."),
    ShellTokenSpec("shell_tab_active_underline", "tab", "Active tab underline/accent."),
    ShellTokenSpec("shell_menu_hover_bg", "menu", "Hover surface for icon menu buttons and menu entries."),
    ShellTokenSpec("shell_menu_open_bg", "menu", "Pressed/open menu button surface."),
    ShellTokenSpec("shell_action_context_bg", "action", "Context label chip background."),
    ShellTokenSpec("shell_action_primary_bg", "action", "Primary action button background."),
    ShellTokenSpec("shell_action_secondary_bg", "action", "Secondary action button background."),
    ShellTokenSpec("shell_action_utility_bg", "action", "Utility button/user chip background."),
)

REQUIRED_SHELL_TOKEN_KEYS: Sequence[str] = tuple(spec.key for spec in REQUIRED_SHELL_TOKEN_SPECS)

REQUIRED_SHELL_OBJECT_NAMES: Sequence[str] = (
    "TabbedWorkspace",
    "MainNavButton",
    "UnifiedActionBar",
    "ActionBarContext",
    "ActionBarButton_save",
    "ActionBarButton_print",
    "ActionBarUtilityButton_theme",
    "ActionBarUserLabel",
)

REQUIRED_SHELL_QSS_MARKERS: Sequence[str] = (
    "Phase354: branded workspace tab cards",
    "QTabWidget#TabbedWorkspace::pane",
    "QTabBar::tab[tabKind=\"main\"]",
    "QTabBar::tab[tabKind=\"sub\"]",
    "Phase354: branded icon menu and action bar runtime",
    "QWidget#IconMenuBar",
    "QPushButton#MainNavButton",
    "QFrame#UnifiedActionBar",
    "QLabel#ActionBarContext",
)


def validate_shell_identity_tokens(tokens: Mapping[str, str]) -> Dict[str, List[str]]:
    issues: Dict[str, List[str]] = {}
    for key in REQUIRED_SHELL_TOKEN_KEYS:
        if not str(tokens.get(key, "")).strip():
            issues.setdefault("missing_shell_tokens", []).append(key)
    return issues


def shell_identity_matrix(tokens: Mapping[str, str] | None = None) -> List[Dict[str, object]]:
    token_map = tokens or {}
    rows: List[Dict[str, object]] = []
    for spec in REQUIRED_SHELL_TOKEN_SPECS:
        rows.append({
            "kind": "token",
            "key": spec.key,
            "role": spec.role,
            "description": spec.description,
            "present": spec.key in token_map if token_map else True,
        })
    for object_name in REQUIRED_SHELL_OBJECT_NAMES:
        rows.append({
            "kind": "object",
            "key": object_name,
            "role": "runtime_object",
            "description": "Required shell runtime object name/property target.",
            "present": True,
        })
    return rows


__all__ = [
    "SHELL_IDENTITY_PHASE",
    "ShellTokenSpec",
    "REQUIRED_SHELL_TOKEN_SPECS",
    "REQUIRED_SHELL_TOKEN_KEYS",
    "REQUIRED_SHELL_OBJECT_NAMES",
    "REQUIRED_SHELL_QSS_MARKERS",
    "validate_shell_identity_tokens",
    "shell_identity_matrix",
]
