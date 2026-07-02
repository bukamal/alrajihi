# -*- coding: utf-8 -*-
from pathlib import Path

from alrajhi_client.features.restaurant.cafe_workspace_activation import (
    CAFE_ENGINE_BACKING,
    CAFE_PAGE_ID,
    CAFE_PERMISSION_KEYS,
    CAFE_SETTINGS_KEY,
    cafe_page_enabled_from_settings,
    cafe_standalone_navigation_contract,
    cafe_uses_shared_restaurant_engine,
)

ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase313_cafe_activation_contract_is_standalone_ui_shared_engine():
    contract = cafe_standalone_navigation_contract()
    assert CAFE_PAGE_ID == "cafe"
    assert CAFE_SETTINGS_KEY == "cafe/enabled"
    assert CAFE_ENGINE_BACKING == "restaurant"
    assert cafe_uses_shared_restaurant_engine() is True
    assert contract["page_id"] == "cafe"
    assert contract["engine_backing"] == "restaurant"
    assert contract["order_type"] == "cafe_quick_order"
    assert "quick_order" in contract["visible_sections"]
    assert "barista" in contract["visible_sections"]
    assert "shift_report" in contract["visible_sections"]
    assert "table_map" in contract["hidden_restaurant_sections"]
    assert "transfer_table" in contract["hidden_restaurant_sections"]
    assert set(CAFE_PERMISSION_KEYS) >= {"cafe.view", "cafe.order", "cafe.payment", "cafe.print", "cafe.report"}


def test_phase313_cafe_visibility_comes_from_cafe_enabled_not_restaurant_enabled():
    assert cafe_page_enabled_from_settings({"cafe/enabled": "true", "restaurant/enabled": "false"}) is True
    assert cafe_page_enabled_from_settings({"cafe/enabled": "false", "restaurant/enabled": "true"}) is False
    assert cafe_page_enabled_from_settings({"cafe": {"enabled": True}}) is True
    assert cafe_page_enabled_from_settings({"cafe": {"enabled": False}}) is False


def test_phase313_main_window_registers_cafe_as_top_level_page_and_navigation():
    main_window = _text("alrajhi_client/views/main_window.py")
    policy = _text("alrajhi_client/workspace/navigation/module_visibility_policy.py")
    settings_tabs = _text("alrajhi_client/features/settings/settings_document_tabs.py")
    settings_widget = _text("alrajhi_client/views/widgets/settings_widget.py")
    i18n = _text("alrajhi_client/i18n/translator.py")

    assert "\'cafe\': (\'alrajhi_client.views.cafe\', \'CafeWorkspaceWidget\')" in main_window
    assert "'cafe': ('restaurant.cafe_workspace_title', 'nav_cafe')" in main_window
    assert "('cafe', CafeWorkspaceWidget)" in main_window
    assert "page_enabled('cafe')" in main_window
    assert "translate('nav_cafe')" in main_window
    assert "self.cafe_shortcut" in main_window and "F10" in main_window
    assert "'cafe': (('cafe/enabled', True),)" in policy
    assert "class CafeSettingsTab" in settings_tabs
    assert "'cafe': CafeSettingsTab" in settings_tabs
    assert "contract_cafe_enabled" in settings_widget
    assert "'cafe/enabled': self.contract_cafe_enabled.isChecked()" in settings_widget
    assert "'nav_cafe': 'الكافي'" in i18n
    assert "'settings.cafe': 'إعدادات الكافي'" in i18n
    assert "'settings_module_cafe': 'تفعيل الكافي'" in i18n


def test_phase313_cafe_workspace_widget_reuses_restaurant_dashboard_without_table_service_leak():
    cafe_widget = _text("alrajhi_client/views/cafe/cafe_workspace_widget.py")
    restaurant_dashboard = _text("alrajhi_client/views/restaurant/restaurant_dashboard.py")

    assert "class CafeWorkspaceWidget(RestaurantDashboard)" in cafe_widget
    assert "workspace_context=\"cafe\"" in cafe_widget
    assert "_standalone_cafe_workspace" in restaurant_dashboard
    assert "self.show_cafe_mode()" in restaurant_dashboard
    assert "self.order_mode_btn.setVisible(False)" in restaurant_dashboard
    assert "self.kitchen_mode_btn.setVisible(False)" in restaurant_dashboard
    assert "self.tables_mode_btn.setVisible(False)" in restaurant_dashboard
    assert "return self.show_cafe_preparation_mode()" in restaurant_dashboard
    assert "return self.show_cafe_report_mode()" in restaurant_dashboard


def test_phase313_cafe_permissions_are_registered_but_alias_to_restaurant_engine():
    document_contract = _text("alrajhi_client/workspace/documents/document_contract.py")
    permission_binder = _text("alrajhi_client/workspace/documents/document_permission_binder.py")

    assert 'document_type="cafe"' in document_contract
    assert 'document_class="views.cafe.cafe_workspace_widget.CafeWorkspaceWidget"' in document_contract
    assert 'gateway="restaurant_gateway"' in document_contract
    assert 'api_resource="/api/restaurant"' in document_contract
    assert 'view="cafe.view"' in document_contract
    assert 'create="cafe.order"' in document_contract
    assert 'update="cafe.payment"' in document_contract
    assert 'print="cafe.print"' in document_contract
    assert 'export="cafe.report"' in document_contract
    assert '"cafe.view": "restaurant_use"' in permission_binder
    assert '"cafe.order": "restaurant_add_line"' in permission_binder
    assert '"cafe.payment": "restaurant_record_payment"' in permission_binder
    assert '"cafe.print": "restaurant_print_receipt"' in permission_binder
    assert '"cafe.report": "restaurant_view_analytics"' in permission_binder


def test_phase313_no_independent_cafe_engine_files_were_added():
    forbidden_names = {
        "cafe_gateway.py",
        "cafe_repository.py",
        "cafe_payment_service.py",
        "cafe_printing_service.py",
    }
    found = {path.name for path in ROOT.rglob("*.py") if path.name in forbidden_names}
    assert not found


def test_phase313_release_gate_registered_and_documented():
    gate = _text("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(313, "STANDALONE_CAFE_WORKSPACE_ACTIVATION")' in gate
    assert '(313, "standalone_cafe_workspace_activation")' in gate
    assert "tests/test_phase313_standalone_cafe_workspace_activation.py" in gate
    assert (ROOT / "PHASE313_STANDALONE_CAFE_WORKSPACE_ACTIVATION.md").exists()
