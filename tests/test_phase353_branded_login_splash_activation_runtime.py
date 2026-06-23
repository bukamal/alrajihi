# -*- coding: utf-8 -*-
"""Phase 353 branded login/splash/activation runtime tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'alrajhi_client'))


def test_first_run_tokens_cover_light_and_dark():
    from theme.brand import get_tokens, BRAND
    from theme.first_run_identity import REQUIRED_FIRST_RUN_TOKEN_KEYS, validate_first_run_tokens

    assert int(BRAND.get('brand_phase', 0)) >= 353
    assert 'first_run_panel_bg' in REQUIRED_FIRST_RUN_TOKEN_KEYS
    assert 'activation_device_bg' in REQUIRED_FIRST_RUN_TOKEN_KEYS
    assert validate_first_run_tokens(get_tokens('light')) == {}
    assert validate_first_run_tokens(get_tokens('dark')) == {}


def test_first_run_runtime_helpers_exist_and_are_wired_textually():
    helper = (ROOT / 'alrajhi_client/ui/first_run_branding.py').read_text(encoding='utf-8')
    for marker in [
        'FIRST_RUN_RUNTIME_PHASE = 353',
        'brand_side_panel',
        'first_run_form_panel',
        'activation_device_panel',
        'set_first_run_primary',
    ]:
        assert marker in helper

    files = {
        'alrajhi_client/views/splash_screen.py': ['apply_first_run_surface(self.container, \'splash\')', 'firstRunStageChip', 'firstRunProgressTrack'],
        # Phase367/368 intentionally supersede the split login runtime with the original single-card login.
        'alrajhi_client/views/dialogs/login_dialog.py': ['Phase367: restored LoginDialog', 'Phase368: password visibility button'],
        'alrajhi_client/views/dialogs/activation_dialog.py': ['brand_side_panel(', 'activation_device_panel', "firstRunSurface', 'activation'", 'set_first_run_primary'],
    }
    for rel, markers in files.items():
        text = (ROOT / rel).read_text(encoding='utf-8')
        for marker in markers:
            assert marker in text


def test_qss_contains_first_run_runtime_surface_markers():
    qss = (ROOT / 'alrajhi_client/theme/qss.py').read_text(encoding='utf-8')
    required = [
        'Phase353: branded first-run split panels and runtime polish',
        'QFrame#firstRunBrandPanel',
        'QFrame#firstRunFormPanel',
        'QLabel#firstRunHeroTitle',
        'QPushButton#firstRunPrimary',
        'QFrame#activationDevicePanel',
        'QProgressBar#firstRunProgressTrack',
    ]
    for marker in required:
        assert marker in qss


def test_phase353_guard_summary_is_clean():
    from workspace.quality.branded_first_run_runtime_contract import branded_first_run_runtime_summary

    summary = branded_first_run_runtime_summary(ROOT)
    assert summary['ready'] is True
    assert summary['issues'] == 0
    assert summary['checks'] >= 35
