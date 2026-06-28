# -*- coding: utf-8 -*-
"""Basit shell chrome visual contract (Phase 406)."""
from __future__ import annotations

BASIT_SHELL_CHROME_CONTRACT = {
    "phase": 406,
    "surfaces": (
        "IconMenuBar",
        "UnifiedActionBar",
        "TabbedWorkspace",
    ),
    "properties": (
        "basitShellChrome",
        "basitShellTabs",
    ),
    "palette_tokens": (
        "basit_shell_bg",
        "basit_shell_menu_bg",
        "basit_shell_active_bg",
        "basit_shell_active_text",
    ),
    "rules": (
        "menu chrome uses Basit blue buttons on Basit toolbar background",
        "home/open/selected states use Basit yellow with red emphasis",
        "shared action bar primary actions use Basit red and utilities use table panels",
        "workspace tabs use Basit blue selected tabs with yellow underline",
    ),
}


def shell_surfaces() -> tuple[str, ...]:
    return BASIT_SHELL_CHROME_CONTRACT["surfaces"]
