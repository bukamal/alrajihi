# -*- coding: utf-8 -*-
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_dashboard_pixel_style_tokens_are_present_and_parseable():
    src = read('alrajhi_client/views/widgets/dashboard_widget.py')
    ast.parse(src)
    assert 'DashboardQuickActionsPanel' in src
    assert 'DashboardCompanyPanel' in src
    assert 'DashboardCashPanel' in src
    assert 'DeveloperBrandPanel' in src
    assert 'SystemBrandDivider' in src
    assert 'font-size: 32px' in src
    assert 'border-radius: 24px' in src
    assert 'QFrame#CashBalanceBox' in src


def test_dashboard_keeps_exchange_rate_sync_and_no_old_identity_copy():
    src = read('alrajhi_client/views/widgets/dashboard_widget.py')
    assert 'self.exchange_rate_input' in src
    assert 'currency.update_rate(code' in src
    assert 'integrated_management_system' in src
    assert 'integrated_management_subtitle' in src
    assert 'developer_identity_caption' not in src
    assert 'هوية النظام والمطوّر' not in src
    assert 'مستقلة عن بيانات الشركة' not in src


def test_dashboard_visual_matching_registered_in_release_gate():
    gate = read('alrajhi_client/workspace/quality/release_gate_contract.py')
    assert '(302, "DASHBOARD_PIXEL_STYLE_VISUAL_MATCHING")' in gate
    assert 'tests/test_phase302_dashboard_pixel_style_visual_matching.py' in gate
    assert 'dashboard_pixel_style_visual_matching' in gate
    assert (ROOT / 'PHASE302_DASHBOARD_PIXEL_STYLE_VISUAL_MATCHING.md').exists()
