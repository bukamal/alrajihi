# -*- coding: utf-8 -*-
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def test_dashboard_removes_rendered_bottom_alerts_strip_but_keeps_compatibility_stub():
    src = read('alrajhi_client/views/widgets/dashboard_widget.py')
    ast.parse(src)
    bottom = src.split('def _build_bottom_grid', 1)[1].split('def _create_quick_actions_panel', 1)[0]
    assert 'self.alerts_panel' not in bottom
    assert 'self.main_layout.addWidget(self.brand_panel)' in bottom
    assert 'lower alerts' in src or 'bottom alerts' in src
    assert 'def _refresh_alerts' in src
    assert 'def _create_alerts_panel' in src
    assert 'return None' in src
    assert 'alert_service' not in src


def test_dashboard_distinguishes_system_identity_from_company_identity():
    src = read('alrajhi_client/views/widgets/dashboard_widget.py')
    assert "DashboardPanel(translate('system_identity')" in src
    assert "DashboardPanel(translate('company_current_info')" in src
    assert 'def _company_has_explicit_info' in src
    assert 'company_fallback_note' in src
    assert "QSettings(\"Alrajhi\", \"Accounting\")" in src
    assert 'logo_png(512)' in src
    assert '_dashboard_product_name()' in src


def test_dashboard_identity_translations_exist():
    src = read('alrajhi_client/i18n/translator.py')
    for key in ('system_identity', 'company_current_info', 'company_info_fallback_note'):
        assert key in src
    assert 'هوية النظام' in src
    assert 'معلومات الشركة الحالية' in src
    assert 'System identity' in src
    assert 'Systemidentität' in src


def test_phase_document_exists():
    assert (ROOT / 'PHASE285_DASHBOARD_IDENTITY_LAYOUT_CLEANUP.md').exists()
