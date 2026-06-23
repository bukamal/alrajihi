# -*- coding: utf-8 -*-
"""Phase 356 branded dialogs/system-window tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'alrajhi_client'))


def test_dialog_identity_tokens_cover_light_and_dark():
    from theme.brand import BRAND, get_tokens
    from theme.dialog_identity import (
        DIALOG_IDENTITY_PHASE,
        REQUIRED_DIALOG_TOKEN_KEYS,
        validate_dialog_identity_tokens,
    )

    assert int(BRAND.get('brand_phase', 0)) >= DIALOG_IDENTITY_PHASE
    assert 'dialog_primary_bg' in REQUIRED_DIALOG_TOKEN_KEYS
    assert 'toast_success_bg' in REQUIRED_DIALOG_TOKEN_KEYS
    assert validate_dialog_identity_tokens(get_tokens('light')) == {}
    assert validate_dialog_identity_tokens(get_tokens('dark')) == {}


def test_dialog_runtime_wiring_markers_are_present():
    files = {
        'alrajhi_client/ui/dialog_branding.py': [
            'apply_branded_dialog',
            'normalize_dialog_buttons',
            'dialogActionRole',
            'brand_message_box',
            'branded_question',
        ],
        'alrajhi_client/views/frameless_dialog.py': [
            'BrandDialogFrame',
            'BrandDialogHeader',
            'BrandDialogTitle',
            'apply_branded_dialog',
        ],
        'alrajhi_client/views/widgets/modern_ui.py': [
            'BrandDialogHeaderCard',
            'apply_branded_dialog(dialog',
            'normalize_dialog_buttons(dialog)',
        ],
        'alrajhi_client/views/widgets/toast_notification.py': [
            'toastType',
            'toast_success_bg',
            'toast_min_width',
        ],
        'alrajhi_client/theme/qss.py': [
            'Phase356: branded dialogs and system windows',
            'QDialog[brandDialog="true"]',
            'QFrame#BrandDialogFrame',
            'QPushButton[dialogActionRole="primary"]',
            'QMessageBox QLabel',
            'QFrame#ToastNotification',
        ],
    }
    for rel, markers in files.items():
        text = (ROOT / rel).read_text(encoding='utf-8')
        for marker in markers:
            assert marker in text


def test_phase356_guard_summary_is_clean():
    from workspace.quality.branded_dialogs_system_windows_contract import branded_dialogs_system_windows_summary

    summary = branded_dialogs_system_windows_summary(ROOT)
    assert summary['ready'] is True
    assert summary['issues'] == 0
    assert summary['checks'] >= 40
