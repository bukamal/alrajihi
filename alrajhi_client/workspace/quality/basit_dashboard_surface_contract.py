# -*- coding: utf-8 -*-
"""Phase402 Basit-inspired dashboard surface contract."""
from __future__ import annotations

BASIT_DASHBOARD_SURFACE_CONTRACT = {
    "phase": 402,
    "surface": "dashboard",
    "goal": "Make the landing dashboard visually consistent with the Basit-inspired POS system.",
    "requirements": [
        "Dashboard root/page are tagged basitInspired.",
        "Daily shortcut buttons use the blue Basit card grammar and unified height.",
        "Dashboard panels use rectangular Basit borders instead of rounded white cards.",
        "Cash balance and exchange-rate boxes follow Basit total/panel surfaces.",
        "The developer/system banner is visually aligned with the same rectangular panel grammar.",
    ],
    "tokens": [
        "basit_blue", "basit_yellow", "basit_red", "basit_dashboard_card_height", "basitPanel", "basitCard",
    ],
}
