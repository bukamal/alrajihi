#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "audit_outputs" / "basit_startup_dialogs_surface_matrix.csv"

CHECKS = [
    ("contract", "alrajhi_client/workspace/quality/basit_startup_dialogs_surface_contract.py", "BASIT_STARTUP_DIALOGS_SURFACE_CONTRACT"),
    ("qss_phase", "alrajhi_client/theme/qss.py", "Phase407: Basit-inspired startup"),
    ("qss_startup", "alrajhi_client/theme/qss.py", 'QFrame#startupCard[basitStartupSurface="true"]'),
    ("qss_login", "alrajhi_client/theme/qss.py", 'QFrame#loginCard[basitFirstRunChrome="true"]'),
    ("qss_activation", "alrajhi_client/theme/qss.py", 'QFrame#activationCard[basitFirstRunChrome="true"]'),
    ("qss_dialog", "alrajhi_client/theme/qss.py", 'QDialog[basitDialogSurface="true"] QFrame#BrandDialogHeader'),
    ("qss_primary", "alrajhi_client/theme/qss.py", 'QDialog[basitDialogSurface="true"] QPushButton[dialogActionRole="primary"]'),
    ("splash_marker", "alrajhi_client/views/splash_screen.py", "basitStartupSurface"),
    ("splash_chip_marker", "alrajhi_client/views/splash_screen.py", "firstRunStageChip"),
    ("login_marker", "alrajhi_client/views/dialogs/login_dialog.py", "basitFirstRunChrome"),
    ("login_primary", "alrajhi_client/views/dialogs/login_dialog.py", "basitPrimaryAction"),
    ("activation_marker", "alrajhi_client/views/dialogs/activation_dialog.py", "basitFirstRunChrome"),
    ("module_apply_brand", "alrajhi_client/views/dialogs/module_activation_dialog.py", "apply_branded_dialog(self, self.windowTitle(), role='module_activation')"),
    ("module_message", "alrajhi_client/views/dialogs/module_activation_dialog.py", "brand_message_box"),
    ("dialog_branding", "alrajhi_client/ui/dialog_branding.py", 'dialog.setProperty("basitDialogSurface", True)'),
    ("message_branding", "alrajhi_client/ui/dialog_branding.py", 'box.setProperty("basitDialogSurface", True)'),
    ("frameless_base", "alrajhi_client/views/frameless_dialog.py", "basitDialogSurface"),
]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    rows = []
    failures = []
    for name, rel, needle in CHECKS:
        ok = needle in read(rel)
        rows.append({"check": name, "path": rel, "needle": needle, "status": "OK" if ok else "FAIL"})
        if not ok:
            failures.append(f"{name}: missing {needle!r} in {rel}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "path", "needle", "status"])
        writer.writeheader()
        writer.writerows(rows)
    if failures:
        print("Phase407 Basit startup/dialogs surface guard failed:")
        for failure in failures:
            print("-", failure)
        return 1
    print(f"Phase407 Basit startup/dialogs surface guard OK ({len(rows)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
