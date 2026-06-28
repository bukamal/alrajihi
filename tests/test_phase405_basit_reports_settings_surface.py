# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_reports_surface_has_basit_toolbar_tabs_tables_and_summary():
    src = read("alrajhi_client/views/widgets/reports_widget.py")
    assert "QMenu, QFrame" in src
    assert "basitReportsSurface" in src
    assert "ReportsFilterToolbar" in src
    assert "basitReportToolbar" in src
    assert "basitReportTabs" in src
    assert "basitReportSummary" in src
    assert "basitReportTable" in src
    assert "basitToolbarButton" in src


def test_settings_surface_has_basit_group_navigation_cards_and_buttons():
    src = read("alrajhi_client/views/widgets/settings_widget.py")
    assert "basitSettingsSurface" in src
    assert "basitSettingsTabs" in src
    assert "basitSettingsGroupTabs" in src
    assert "basitSettingsScrollPage" in src
    assert "basitSettingsCard" in src
    assert "basitSettingsNote" in src
    assert "basitToolbarButton" in src


def test_qss_contains_reports_and_settings_basit_rules():
    qss = read("alrajhi_client/theme/qss.py")
    assert "Phase405: Basit-inspired reports and settings surfaces" in qss
    assert "QFrame#ReportsFilterToolbar[basitReportToolbar" in qss
    assert "QTabWidget[basitReportTabs" in qss
    assert "QLabel#reportSummaryBar[basitReportSummary" in qss
    assert "QWidget#settingsWidget[basitSettingsSurface" in qss
    assert "QGroupBox#settingsCard[basitSettingsCard" in qss


def test_quality_contract_documents_reports_settings_surface():
    contract = read("alrajhi_client/workspace/quality/basit_reports_settings_surface_contract.py")
    assert "BASIT_REPORTS_SETTINGS_SURFACE_CONTRACT" in contract
    assert "reports" in contract
    assert "settings" in contract
    assert "basitReportSummary" in contract
