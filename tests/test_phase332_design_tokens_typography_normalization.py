# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase332_brand_tokens_define_typography_and_shell_metrics():
    from theme.brand import BRAND
    design_system = read("alrajhi_client/ui/design_system.py")

    assert BRAND["font_size_body_pt"] >= 11
    assert BRAND["nav_height"] >= 70
    assert BRAND["nav_font_px"] >= 12
    assert BRAND["nav_icon_size"] >= 26
    assert BRAND["action_bar_height"] >= 50
    assert BRAND["action_button_icon"] >= 18
    assert "FONT_BODY_PT = int(BRAND.get('font_size_body_pt'" in design_system
    assert "FONT_CAPTION_PX = int(BRAND.get('font_size_caption_px'" in design_system


def test_phase332_global_qss_consumes_design_tokens_not_tiny_literals():
    qss = read("alrajhi_client/theme/qss.py")
    assert "body_pt = BRAND.get('font_size_body_pt'" in qss
    assert "nav_px = BRAND.get('nav_font_px'" in qss
    assert "action_px = BRAND.get('action_button_font_px'" in qss
    assert "input_min = BRAND.get('input_min_height'" in qss
    assert "font-size: 9px" not in qss
    assert "font-size: 10pt" not in qss
    assert "QMenuBar" in qss and "font-size: {nav_px}px" in qss


def test_phase332_main_navigation_uses_tokenized_larger_shell_metrics():
    main_window = read("alrajhi_client/views/main_window.py")
    assert "NAV_BAR_HEIGHT = int(BRAND.get('nav_height', 74))" in main_window
    assert "NAV_ICON_SIZE = int(BRAND.get('nav_icon_size', 26))" in main_window
    assert "def navigation_bar_stylesheet()" in main_window
    assert "self.menu_bar.setFixedHeight(NAV_BAR_HEIGHT)" in main_window
    assert "btn.setIconSize(QSize(NAV_ICON_SIZE, NAV_ICON_SIZE))" in main_window
    assert "btn.setMinimumHeight(NAV_BUTTON_HEIGHT)" in main_window
    assert "font-size: 9px" not in main_window
    assert "self.menu_bar.setFixedHeight(60)" not in main_window


def test_phase332_action_bar_uses_tokenized_height_icons_and_fonts():
    action_bar = read("alrajhi_client/shell/unified_action_bar.py")
    assert "ACTION_BAR_HEIGHT = int(BRAND.get('action_bar_height', 52))" in action_bar
    assert "ACTION_BUTTON_ICON = int(BRAND.get('action_button_icon', 18))" in action_bar
    assert "self.setFixedHeight(ACTION_BAR_HEIGHT)" in action_bar
    assert "QSize(ACTION_BUTTON_ICON, ACTION_BUTTON_ICON)" in action_bar
    assert "font-size: {ACTION_BUTTON_FONT_PX}px" in action_bar
    assert "min-height: {ACTION_BUTTON_MIN_HEIGHT}px" in action_bar
    assert "font-size: 10px" not in action_bar
    assert "self.setFixedHeight(ACTION_BAR_HEIGHT)" in action_bar


def test_phase332_release_gate_registered_and_documented():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(332, "DESIGN_TOKENS_TYPOGRAPHY_NORMALIZATION")' in gate
    assert "tests/test_phase332_design_tokens_typography_normalization.py" in gate
    assert 'ReleaseGateCheck("design_tokens_typography_normalization"' in gate
    assert (ROOT / "PHASE332_DESIGN_TOKENS_TYPOGRAPHY_NORMALIZATION.md").exists()
