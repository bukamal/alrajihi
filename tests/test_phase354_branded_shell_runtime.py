# -*- coding: utf-8 -*-
"""Phase 354 branded shell runtime tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'alrajhi_client'))


def test_shell_tokens_cover_light_and_dark():
    from theme.brand import BRAND, get_tokens
    from theme.shell_identity import REQUIRED_SHELL_TOKEN_KEYS, SHELL_IDENTITY_PHASE, validate_shell_identity_tokens

    assert int(BRAND.get('brand_phase', 0)) >= SHELL_IDENTITY_PHASE
    assert 'shell_tab_main_badge_bg' in REQUIRED_SHELL_TOKEN_KEYS
    assert 'shell_action_primary_bg' in REQUIRED_SHELL_TOKEN_KEYS
    assert validate_shell_identity_tokens(get_tokens('light')) == {}
    assert validate_shell_identity_tokens(get_tokens('dark')) == {}


def test_tab_label_policy_marks_main_and_sub_tabs():
    import importlib.util
    spec = importlib.util.spec_from_file_location('phase354_tab_label_policy', ROOT / 'alrajhi_client/shell/tab_label_policy.py')
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    import sys as _sys
    _sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    BRANDED_TAB_PHASE = module.BRANDED_TAB_PHASE
    compose_tab_label = module.compose_tab_label
    tab_kind_for_id = module.tab_kind_for_id

    assert BRANDED_TAB_PHASE >= 354
    assert tab_kind_for_id('sales_invoices') == 'main'
    assert tab_kind_for_id('invoice:sale:new') == 'sub'
    assert compose_tab_label('sales_invoices', 'فواتير البيع').display_text == 'فواتير البيع'
    assert compose_tab_label('invoice:sale:new', 'فاتورة بيع جديدة').display_text == 'فاتورة بيع جديدة'


def test_shell_runtime_files_are_wired_textually():
    files = {
        'alrajhi_client/shell/tab_workspace.py': ['BRANDED_TABS_PHASE = 354', 'compose_tab_label', '_apply_tab_identity', 'setTabData', 'brandedTabs'],
        'alrajhi_client/shell/unified_action_bar.py': ['BRANDED_ACTION_BAR_PHASE = 354', 'shellChromeRole', 'ActionBarButton_save', 'ActionBarButton_print'],
        'alrajhi_client/views/main_window.py': ['navigation_bar_stylesheet', 'shellChromeRole', 'MainNavButton', 'menuLabel'],
        'alrajhi_client/theme/qss.py': ['Phase354: branded workspace tab cards', 'Phase354: branded icon menu and action bar runtime'],
    }
    for rel, markers in files.items():
        text = (ROOT / rel).read_text(encoding='utf-8')
        for marker in markers:
            assert marker in text


def test_phase354_guard_summary_is_clean():
    from workspace.quality.branded_shell_runtime_contract import branded_shell_runtime_summary

    summary = branded_shell_runtime_summary(ROOT)
    assert summary['ready'] is True
    assert summary['issues'] == 0
    assert summary['checks'] >= 45
