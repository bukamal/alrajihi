# -*- coding: utf-8 -*-
"""Phase 352 brand identity token system tests."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_brand_identity_tokens_cover_light_and_dark():
    import sys
    sys.path.insert(0, str(ROOT / 'alrajhi_client'))
    from theme.brand import get_tokens
    from theme.identity import REQUIRED_BRAND_TOKEN_KEYS, validate_brand_identity_tokens

    assert 'brand_navy' in REQUIRED_BRAND_TOKEN_KEYS
    assert 'tab_active_bg' in REQUIRED_BRAND_TOKEN_KEYS
    assert 'dialog_header_bg' in REQUIRED_BRAND_TOKEN_KEYS
    assert validate_brand_identity_tokens(get_tokens('light')) == {}
    assert validate_brand_identity_tokens(get_tokens('dark')) == {}


def test_qss_contains_branded_surfaces_and_chrome():
    qss = (ROOT / 'alrajhi_client/theme/qss.py').read_text(encoding='utf-8')
    required = [
        'Phase352: branded main/sub tab labels',
        'QTabBar::tab:selected',
        'QTabBar::close-button:hover',
        'Phase352: branded menu and action chrome',
        'Phase352: first-run and licensing identity surfaces',
        'Phase352: branded dialogs and system windows',
        'QFrame#startupCard',
        'QFrame#loginCard',
        'QFrame#activationCard',
        'QLabel#brandMark',
    ]
    for marker in required:
        assert marker in qss


def test_first_run_screens_consume_brand_metrics():
    files = {
        'alrajhi_client/views/splash_screen.py': ['brandMark', 'brand_logo_large_px', 'splash_width'],
        # Phase367/368 intentionally restored LoginDialog to the pre-Phase350 card while keeping QSS/tokens.
        'alrajhi_client/views/dialogs/login_dialog.py': ['Phase367: restored LoginDialog', 'Phase368: password visibility button'],
        'alrajhi_client/views/dialogs/activation_dialog.py': ['brandMark', 'brand_logo_login_px', 'activation_card_width'],
        'alrajhi_client/ui/design_system.py': ['brand_gradient', 'apply_visual_role', 'BRAND_BUTTON_MIN_HEIGHT'],
    }
    for rel, markers in files.items():
        text = (ROOT / rel).read_text(encoding='utf-8')
        for marker in markers:
            assert marker in text


def test_phase352_guard_outputs_clean_matrix():
    import sys
    sys.path.insert(0, str(ROOT / 'alrajhi_client'))
    from workspace.quality.brand_identity_visual_contract import brand_identity_visual_summary

    summary = brand_identity_visual_summary(ROOT)
    assert summary['ready'] is True
    assert summary['issues'] == 0
    assert summary['checks'] >= 40
