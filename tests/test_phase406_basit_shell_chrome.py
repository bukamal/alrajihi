# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_basit_shell_tokens_exist_in_brand_palette():
    src = read("alrajhi_client/theme/brand.py")
    for token in (
        "basit_shell_nav_height",
        "basit_shell_action_height",
        "basit_shell_tab_height",
        "basit_shell_bg",
        "basit_shell_menu_bg",
        "basit_shell_active_bg",
        "basit_shell_active_text",
    ):
        assert token in src


def test_main_navigation_uses_basit_chrome_styles():
    src = read("alrajhi_client/views/main_window.py")
    assert "Phase406: Basit-inspired shell navigation chrome" in src
    assert "basit_shell_nav_height" in src
    assert "basitShellChrome" in src
    assert "basit_shell_menu_bg" in src
    assert "basit_shell_active_bg" in src


def test_action_bar_uses_basit_chrome_contract():
    src = read("alrajhi_client/shell/unified_action_bar.py")
    assert "basit_shell_action_height" in src
    assert "basitShellChrome" in src
    assert "Phase406: Basit-inspired shared action bar runtime" in src
    assert "basit_yellow" in src
    assert "basit_red" in src


def test_workspace_tabs_use_basit_contract():
    src = read("alrajhi_client/shell/tab_workspace.py")
    assert "basitShellTabs" in src
    assert "basit_shell_tab_height" in src
    assert "Phase406: Basit-inspired workspace tab cards" in src
    assert "basit_yellow" in src
    assert "basit_blue" in src


def test_global_qss_has_basit_shell_fallback():
    src = read("alrajhi_client/theme/qss.py")
    assert "Phase406: Basit-inspired shell chrome fallback" in src
    assert 'QWidget#IconMenuBar[basitShellChrome="true"]' in src
    assert 'QFrame#UnifiedActionBar[basitShellChrome="true"]' in src
    assert 'QTabWidget#TabbedWorkspace[basitShellTabs="true"]' in src


def test_contract_file_documents_phase406():
    src = read("alrajhi_client/workspace/quality/basit_shell_chrome_contract.py")
    assert "BASIT_SHELL_CHROME_CONTRACT" in src
    assert "IconMenuBar" in src
    assert "UnifiedActionBar" in src
    assert "TabbedWorkspace" in src
