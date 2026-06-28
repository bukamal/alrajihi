# -*- coding: utf-8 -*-
"""Phase409 Basit-inspired final acceptance contract.

This is a static, import-safe contract used by release guards to ensure the
Basit-inspired UI conversion is complete across runtime UI, printing, shell,
startup and governance surfaces before creating a release-candidate archive.
"""
from __future__ import annotations

BASIT_FINAL_ACCEPTANCE_CONTRACT = {
    "phase": 409,
    "name": "basit_final_acceptance_audit",
    "purpose": "Lock the Basit-inspired visual system behind one final acceptance gate.",
    "required_layers": (
        "theme_tokens",
        "restaurant_pos",
        "dashboard",
        "transaction_documents",
        "management_lists",
        "reports_settings",
        "shell_chrome",
        "startup_dialogs",
        "printing_exports",
        "release_gate",
    ),
    "required_phase_contracts": (
        "BASIT_VISUAL_SYSTEM_CONTRACT",
        "BASIT_DASHBOARD_SURFACE_CONTRACT",
        "BASIT_TRANSACTION_SURFACE_CONTRACT",
        "BASIT_MANAGEMENT_SURFACE_CONTRACT",
        "BASIT_REPORTS_SETTINGS_SURFACE_CONTRACT",
        "BASIT_SHELL_CHROME_CONTRACT",
        "BASIT_STARTUP_DIALOGS_SURFACE_CONTRACT",
        "BASIT_PRINTING_SURFACE_CONTRACT",
    ),
    "acceptance_rule": (
        "Every Basit visual layer from Phase401 to Phase408 must have a contract, "
        "a guard/test entry, QSS/theme markers, and release-gate coverage."
    ),
    "audit_outputs": (
        "tools/audit_outputs/basit_final_acceptance_matrix.csv",
        "tools/audit_outputs/basit_final_acceptance_report.md",
    ),
}


def required_layers() -> tuple[str, ...]:
    return tuple(BASIT_FINAL_ACCEPTANCE_CONTRACT["required_layers"])
