# -*- coding: utf-8 -*-
"""Phase 358 login layout stability tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'alrajhi_client'))


def test_login_dialog_uses_stable_centered_layout_not_split_overlap():
    text = (ROOT / 'alrajhi_client/views/dialogs/login_dialog.py').read_text(encoding='utf-8')
    assert "loginLayout', 'stable_centered'" in text
    assert 'QVBoxLayout(self.content_widget)' in text
    assert 'login_brand_header(' in text
    assert 'QGridLayout(options_panel)' in text
    assert 'root_layout = QHBoxLayout(self.content_widget)' not in text
    assert 'root_layout.addWidget(self.brand_panel, 0)' not in text
    assert "QPushButton(translate('switch_account'))" not in text


def test_login_helper_and_qss_have_stable_header_markers():
    helper = (ROOT / 'alrajhi_client/ui/first_run_branding.py').read_text(encoding='utf-8')
    qss = (ROOT / 'alrajhi_client/theme/qss.py').read_text(encoding='utf-8')
    for marker in ['login_brand_header', 'firstRunLoginHeader', 'firstRunLoginLogo', 'firstRunLoginModeChip']:
        assert marker in helper
    for marker in ['Phase358: stable centered login layout', 'QFrame#firstRunLoginHeader', 'QFrame#loginOptionsPanel', 'QPushButton#loginPasswordToggle']:
        assert marker in qss


def test_phase358_qss_runtime_generation_is_safe_for_light_and_dark():
    from theme.brand import get_tokens, BRAND
    from theme.qss import build_global_qss

    assert int(BRAND.get('brand_phase', 0)) >= 358
    for theme in ('light', 'dark'):
        qss = build_global_qss(get_tokens(theme))
        assert 'QFrame#firstRunLoginHeader' in qss
        assert 'QPushButton#loginPasswordToggle' in qss


def test_phase358_guard_summary_is_clean():
    from workspace.quality.login_layout_stability_contract import login_layout_stability_summary

    summary = login_layout_stability_summary(ROOT)
    assert summary['ready'] is True
    assert summary['issues'] == 0
    assert summary['checks'] >= 25
