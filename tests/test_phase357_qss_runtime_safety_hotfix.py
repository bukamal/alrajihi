# -*- coding: utf-8 -*-
"""Phase 357 QSS runtime f-string safety tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'alrajhi_client'))


def test_global_qss_generates_for_light_and_dark_without_nameerror():
    from theme.brand import get_tokens
    from theme.qss import build_global_qss

    for theme in ('light', 'dark'):
        qss = build_global_qss(get_tokens(theme))
        assert 'QTabWidget#TabbedWorkspace::pane {' in qss
        assert 'QFrame#UnifiedActionBar {' in qss
        assert 'QDialog[brandDialog="true"]' in qss
        assert 'border: 1px solid' in qss


def test_phase357_source_keeps_literal_qss_braces_escaped():
    text = (ROOT / 'alrajhi_client/theme/qss.py').read_text(encoding='utf-8')
    assert 'QTabWidget#TabbedWorkspace::pane {{' in text
    assert 'QFrame#UnifiedActionBar {{' in text
    assert 'QPushButton#MainNavButton:hover {{' in text
    assert 'QFrame#UnifiedActionBar QToolButton[shellChromeRole="primary"] {{' in text


def test_phase357_guard_summary_is_clean():
    from workspace.quality.qss_runtime_safety_contract import qss_runtime_safety_summary

    summary = qss_runtime_safety_summary(ROOT)
    assert summary['ready'] is True
    assert summary['issues'] == 0
    assert summary['checks'] >= 15
