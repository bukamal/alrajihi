# -*- coding: utf-8 -*-
from pathlib import Path

from alrajhi_client.features.restaurant.cafe_workspace_activation import (
    CAFE_EMBEDDED_RESTAURANT_ENTRY_ALLOWED,
    cafe_is_decoupled_from_restaurant_visible_shell,
    cafe_standalone_navigation_contract,
)

ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase314_cafe_contract_is_standalone_not_embedded_in_restaurant_shell():
    contract = cafe_standalone_navigation_contract()

    assert CAFE_EMBEDDED_RESTAURANT_ENTRY_ALLOWED is False
    assert cafe_is_decoupled_from_restaurant_visible_shell() is True
    assert contract["page_id"] == "cafe"
    assert contract["engine_backing"] == "restaurant"
    assert contract["embedded_restaurant_entry_allowed"] is False
    assert "quick_order" in contract["visible_sections"]
    assert "barista" in contract["visible_sections"]
    assert "shift_report" in contract["visible_sections"]
    assert "table_map" in contract["hidden_restaurant_sections"]
    assert "merge_tables" in contract["hidden_restaurant_sections"]


def test_phase314_restaurant_toolbar_no_longer_adds_cafe_mode_button():
    dashboard = _text("alrajhi_client/views/restaurant/restaurant_dashboard.py")

    # Keep the attribute and cafe methods only for the standalone CafeWorkspaceWidget,
    # but do not add the cafe entry to the restaurant toolbar.
    assert "self.cafe_mode_btn = QPushButton" in dashboard
    assert "self.cafe_mode_btn.setVisible(False)" in dashboard
    assert "header.addWidget(self.cafe_mode_btn)" not in dashboard
    assert "self.cafe_mode_btn.setVisible(bool(self._ui_settings.get(\"cafe_enabled\"" not in dashboard
    assert "Cafe is intentionally not added to the restaurant header after Phase 314" in dashboard


def test_phase314_cafe_actions_are_guarded_to_standalone_workspace_only():
    dashboard = _text("alrajhi_client/views/restaurant/restaurant_dashboard.py")

    assert "def show_cafe_mode(self):\n        if not self._standalone_cafe_workspace:\n            return" in dashboard
    assert "def start_new_cafe_order(self):\n        if not self._standalone_cafe_workspace:\n            return" in dashboard
    assert "def show_cafe_preparation_mode(self):\n        if not self._standalone_cafe_workspace:\n            return" in dashboard
    assert "def show_cafe_report_mode(self):\n        if not self._standalone_cafe_workspace:\n            return" in dashboard
    assert "self.cafe_shell_card.setVisible(bool(self._standalone_cafe_workspace" in dashboard


def test_phase314_standalone_cafe_page_still_exists_and_uses_settings_visibility():
    main_window = _text("alrajhi_client/views/main_window.py")
    cafe_widget = _text("alrajhi_client/views/cafe/cafe_workspace_widget.py")
    policy = _text("alrajhi_client/workspace/navigation/module_visibility_policy.py")

    assert "\'cafe\': (\'alrajhi_client.views.cafe\', \'CafeWorkspaceWidget\')" in main_window
    assert "('cafe', CafeWorkspaceWidget)" in main_window
    assert "page_enabled('cafe')" in main_window
    assert "class CafeWorkspaceWidget(RestaurantDashboard)" in cafe_widget
    assert "workspace_context=\"cafe\"" in cafe_widget
    assert "'cafe': (('cafe/enabled', True),)" in policy


def test_phase314_release_gate_registered_and_documented():
    gate = _text("alrajhi_client/workspace/quality/release_gate_contract.py")

    assert '(314, "RESTAURANT_CAFE_UI_DECOUPLING_HOTFIX")' in gate
    assert '(314, "restaurant_cafe_ui_decoupling_hotfix")' in gate
    assert "tests/test_phase314_restaurant_cafe_ui_decoupling_hotfix.py" in gate
    assert (ROOT / "PHASE314_RESTAURANT_CAFE_UI_DECOUPLING_HOTFIX.md").exists()
