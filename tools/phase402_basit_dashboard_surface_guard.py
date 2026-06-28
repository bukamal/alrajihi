#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "audit_outputs" / "basit_dashboard_surface_matrix.csv"

CHECKS = [
    ("contract_exists", "alrajhi_client/workspace/quality/basit_dashboard_surface_contract.py", "BASIT_DASHBOARD_SURFACE_CONTRACT"),
    ("dashboard_root_basit", "alrajhi_client/views/widgets/dashboard_widget.py", "self.setProperty('basitInspired', True)"),
    ("dashboard_page_basit", "alrajhi_client/views/widgets/dashboard_widget.py", "page.setProperty('basitInspired', True)"),
    ("quick_panel_basit", "alrajhi_client/views/widgets/dashboard_widget.py", "QFrame#DashboardQuickActionsPanel { background: #edf2f7; border: 1px solid #aab8cc; border-radius: 2px; }"),
    ("shortcut_height_token", "alrajhi_client/views/widgets/dashboard_widget.py", "BRAND.get('basit_dashboard_card_height', 96)"),
    ("shortcut_visual_role", "alrajhi_client/views/widgets/dashboard_widget.py", "btn.setProperty('visualRole', 'dashboard_shortcut')"),
    ("shortcut_basit_card", "alrajhi_client/views/widgets/dashboard_widget.py", "btn.setProperty('basitCard', True)"),
    ("cash_panel_basit", "alrajhi_client/views/widgets/dashboard_widget.py", "QFrame#DashboardCashPanel { background: #edf2f7; border: 1px solid #aab8cc; border-radius: 2px; }"),
    ("cash_balance_basit_total", "alrajhi_client/views/widgets/dashboard_widget.py", "balance_box.setProperty('basitTotalFooter', True)"),
    ("brand_panel_basit", "alrajhi_client/views/widgets/dashboard_widget.py", "QFrame#DeveloperBrandPanel {"),
    ("quick_action_class_basit", "alrajhi_client/views/widgets/dashboard_legacy_components.py", "self.setProperty('visualRole', 'dashboard_shortcut')"),
    ("dashboard_panel_class_basit", "alrajhi_client/views/widgets/dashboard_legacy_components.py", "self.setProperty('basitPanel', True)"),
]


def main() -> int:
    rows = []
    issues = []
    for name, rel, needle in CHECKS:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        ok = needle in text
        rows.append({"check": name, "path": rel, "needle": needle, "status": "OK" if ok else "FAIL"})
        if not ok:
            issues.append(f"{name}: missing {needle!r} in {rel}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["check", "path", "needle", "status"])
        writer.writeheader()
        writer.writerows(rows)
    if issues:
        print("Phase402 Basit dashboard surface guard failed:")
        for issue in issues:
            print("-", issue)
        return 1
    print(f"Phase402 Basit dashboard surface guard OK ({len(rows)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
