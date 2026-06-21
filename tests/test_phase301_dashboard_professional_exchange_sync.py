# -*- coding: utf-8 -*-
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_dashboard_uses_professional_three_card_layout_and_integrated_banner():
    src = read('alrajhi_client/views/widgets/dashboard_widget.py')
    ast.parse(src)
    assert 'DashboardQuickActionsPanel' in src
    assert 'DashboardCompanyPanel' in src
    assert 'DashboardCashPanel' in src
    assert "translate('integrated_management_system')" in src
    assert "translate('integrated_management_subtitle')" in src
    assert 'developer_identity_caption' not in src
    assert 'هوية النظام والمطوّر' not in src


def test_dashboard_exchange_rate_is_editable_and_persisted_through_currency_manager():
    src = read('alrajhi_client/views/widgets/dashboard_widget.py')
    assert 'QLineEdit' in src
    assert 'self.exchange_rate_input' in src
    assert 'def _save_exchange_rate_from_dashboard' in src
    assert 'currency.update_rate(code' in src
    currency_src = read('alrajhi_client/currency.py')
    assert 'self._cache_rate(currency_code, rate_to_usd)' in currency_src


def test_dashboard_translations_cover_three_languages():
    i18n = read('alrajhi_client/i18n/translator.py')
    for key in (
        'integrated_management_subtitle',
        'invalid_exchange_rate',
        'exchange_rate_updated',
        'exchange_rate_update_failed',
        'exchange_rate_base_currency_no_update',
    ):
        assert key in i18n
    assert 'للمحاسبة والمبيعات والمشتريات والمخزون والتصنيع' in i18n
    assert 'Für Buchhaltung' in i18n
    assert 'For accounting' in i18n


def test_phase_document_exists():
    assert (ROOT / 'PHASE301_DASHBOARD_PROFESSIONAL_EXCHANGE_SYNC.md').exists()
