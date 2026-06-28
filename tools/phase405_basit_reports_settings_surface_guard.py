#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "audit_outputs" / "basit_reports_settings_surface_matrix.csv"

CHECKS = [
    ("contract_exists", "alrajhi_client/workspace/quality/basit_reports_settings_surface_contract.py", "BASIT_REPORTS_SETTINGS_SURFACE_CONTRACT"),
    ("reports_imports_frame", "alrajhi_client/views/widgets/reports_widget.py", "QMenu, QFrame"),
    ("reports_root_property", "alrajhi_client/views/widgets/reports_widget.py", "basitReportsSurface"),
    ("reports_toolbar_frame", "alrajhi_client/views/widgets/reports_widget.py", "ReportsFilterToolbar"),
    ("reports_toolbar_property", "alrajhi_client/views/widgets/reports_widget.py", "basitReportToolbar"),
    ("reports_action_buttons", "alrajhi_client/views/widgets/reports_widget.py", "basitToolbarButton"),
    ("reports_tabs_property", "alrajhi_client/views/widgets/reports_widget.py", "basitReportTabs"),
    ("reports_summary_property", "alrajhi_client/views/widgets/reports_widget.py", "basitReportSummary"),
    ("reports_tables_property", "alrajhi_client/views/widgets/reports_widget.py", "basitReportTable"),
    ("settings_root_property", "alrajhi_client/views/widgets/settings_widget.py", "basitSettingsSurface"),
    ("settings_tabs_property", "alrajhi_client/views/widgets/settings_widget.py", "basitSettingsTabs"),
    ("settings_group_tabs_property", "alrajhi_client/views/widgets/settings_widget.py", "basitSettingsGroupTabs"),
    ("settings_card_property", "alrajhi_client/views/widgets/settings_widget.py", "basitSettingsCard"),
    ("settings_action_buttons", "alrajhi_client/views/widgets/settings_widget.py", "basitToolbarButton"),
    ("qss_phase405", "alrajhi_client/theme/qss.py", "Phase405: Basit-inspired reports and settings surfaces"),
    ("qss_report_toolbar", "alrajhi_client/theme/qss.py", "QFrame#ReportsFilterToolbar[basitReportToolbar"),
    ("qss_report_summary", "alrajhi_client/theme/qss.py", "QLabel#reportSummaryBar[basitReportSummary"),
    ("qss_settings_card", "alrajhi_client/theme/qss.py", "QGroupBox#settingsCard[basitSettingsCard"),
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
        print("Phase405 Basit reports/settings surface guard failed:")
        for issue in issues:
            print("-", issue)
        return 1
    print(f"Phase405 Basit reports/settings surface guard OK ({len(rows)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
