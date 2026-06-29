# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.shell_header_action_bar_visual_consolidation_contract import phase446_shell_header_action_bar_visual_consolidation_summary


def test_phase446_shell_visual_contract_ready():
    summary = phase446_shell_header_action_bar_visual_consolidation_summary(ROOT)
    assert summary["ready"], summary["details"]
    assert summary["issues"] == 0


def test_navigation_bar_uses_calm_identity_tokens():
    src = (ROOT / "alrajhi_client/views/main_window.py").read_text(encoding="utf-8")
    assert "shell_navigation_button_bg" in src
    assert "shell_navigation_button_hover_bg" in src
    assert "background: {basit_blue};" not in src
    assert "Phase446: calm, centralized shell navigation chrome." in src


def test_unified_action_bar_is_secondary_chrome():
    src = (ROOT / "alrajhi_client/shell/unified_action_bar.py").read_text(encoding="utf-8")
    assert "BRANDED_ACTION_BAR_PHASE = 446" in src
    assert "shell_action_secondary_bg_phase446" in src
    assert "Phase446: global action bar is secondary shell chrome" in src
    assert "background: {basit_red};" not in src
