# -*- coding: utf-8 -*-
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_dashboard_has_visible_professional_three_card_layout_not_placeholder_only():
    src = read('alrajhi_client/views/widgets/dashboard_widget.py')
    ast.parse(src)
    middle = src.split('def _build_middle_grid', 1)[1].split('def _build_bottom_grid', 1)[0]
    assert 'DashboardQuickActionsPanel' in src
    assert 'DashboardCompanyPanel' in src
    assert 'DashboardCashPanel' in src
    assert 'setMaximumHeight(430)' in middle
    assert 'row.addWidget(self.project_panel, 5)' in middle
    assert 'row.addWidget(self.company_panel, 4)' in middle
    assert 'row.addWidget(self.quick_panel, 5)' in middle


def test_dashboard_bottom_alerts_are_defensively_hidden_not_rendered():
    src = read('alrajhi_client/views/widgets/dashboard_widget.py')
    assert "return None" in src.split('def _create_alerts_panel', 1)[1].split('def _create_company_info_panel', 1)[0]
    refresh = src.split('def _refresh_alerts', 1)[1].split('def _toggle_cash_movement_mode', 1)[0]
    assert "setVisible(False)" in refresh
    assert "self.main_layout.addWidget(self.brand_panel)" in src
    assert "self.main_layout.addWidget(self.alerts_panel)" not in src


def test_system_identity_band_is_compact_and_not_company_fallback():
    src = read('alrajhi_client/views/widgets/dashboard_widget.py')
    brand = src.split('def _create_brand_panel', 1)[1].split('def _create_health_panel', 1)[0]
    assert 'SystemBrandLogoBox' in brand
    assert 'SystemBrandTitle' in brand
    assert 'integrated_management_subtitle' in brand
    assert 'setMaximumHeight(190)' in brand
    assert 'QHBoxLayout()' in brand
    assert 'company_' not in brand.lower()


def test_phase286_translations_and_release_gate_registration_exist():
    i18n = read('alrajhi_client/i18n/translator.py')
    assert 'integrated_management_subtitle' in i18n
    assert 'نظام إدارة متكامل' in i18n
    gate = read('alrajhi_client/workspace/quality/release_gate_contract.py')
    assert 'PHASE286_DASHBOARD_VISIBLE_PROFESSIONAL_LAYOUT' in gate
    assert 'test_phase286_dashboard_visible_professional_layout.py' in gate
    assert (ROOT / 'PHASE286_DASHBOARD_VISIBLE_PROFESSIONAL_LAYOUT.md').exists()
