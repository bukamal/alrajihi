# -*- coding: utf-8 -*-
"""Phase 407 Basit startup/dialog surface contract.

The Basit-inspired visual system must not stop at workspace pages.  First-run
surfaces, login, activation and system dialogs are entry points and therefore
need the same blue/yellow/red operational identity while preserving validation,
licensing and authentication logic.
"""
from __future__ import annotations

BASIT_STARTUP_DIALOGS_SURFACE_CONTRACT = {
    "phase": 407,
    "surfaces": (
        "startup_splash",
        "login_dialog",
        "activation_dialog",
        "module_activation_dialog",
        "frameless_dialog_base",
        "message_box",
    ),
    "required_properties": (
        "basitStartupSurface",
        "basitFirstRunChrome",
        "basitDialogSurface",
        "dialogActionRole",
    ),
    "color_roles": (
        "basit_blue",
        "basit_yellow",
        "basit_red",
        "basit_canvas",
        "basit_toolbar_border",
    ),
}


def expected_surfaces() -> tuple[str, ...]:
    return tuple(BASIT_STARTUP_DIALOGS_SURFACE_CONTRACT["surfaces"])
