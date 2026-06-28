# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_dashboard_root_and_page_are_basit_surfaces():
    src = read("alrajhi_client/views/widgets/dashboard_widget.py")
    assert "self.setProperty('basitInspired', True)" in src
    assert "page.setProperty('basitInspired', True)" in src
    assert "QFrame#DashboardQuickActionsPanel { background: #edf2f7; border: 1px solid #aab8cc; border-radius: 2px; }" in src


def test_daily_shortcuts_use_basit_card_grammar_and_metrics():
    src = read("alrajhi_client/views/widgets/dashboard_widget.py")
    legacy = read("alrajhi_client/views/widgets/dashboard_legacy_components.py")
    assert "BRAND.get('basit_dashboard_card_height', 96)" in src
    assert "btn.setProperty('visualRole', 'dashboard_shortcut')" in src
    assert "btn.setProperty('basitCard', True)" in src
    assert "self.setProperty('visualRole', 'dashboard_shortcut')" in legacy
    assert "basit_blue" in legacy
    assert "border-radius: 3px" in legacy


def test_dashboard_cash_company_and_brand_panels_use_basit_rectangles():
    src = read("alrajhi_client/views/widgets/dashboard_widget.py")
    assert "QFrame#DashboardCompanyPanel { background: #edf2f7; border: 1px solid #aab8cc; border-radius: 2px; }" in src
    assert "QFrame#DashboardCashPanel { background: #edf2f7; border: 1px solid #aab8cc; border-radius: 2px; }" in src
    assert "balance_box.setProperty('basitTotalFooter', True)" in src
    assert "currency_box.setProperty('basitPanel', True)" in src
    assert "panel.setProperty('basitPanel', True)" in src


def test_quality_contract_documents_dashboard_visual_stage():
    contract = read("alrajhi_client/workspace/quality/basit_dashboard_surface_contract.py")
    assert "BASIT_DASHBOARD_SURFACE_CONTRACT" in contract
    assert "dashboard" in contract
    assert "basit_dashboard_card_height" in contract
