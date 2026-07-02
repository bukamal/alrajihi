# -*- coding: utf-8 -*-
from pathlib import Path

from alrajhi_client.features.apparel import (
    APPAREL_ENGINE_BACKING,
    APPAREL_PAGE_ID,
    APPAREL_SETTINGS_KEY,
    apparel_page_enabled_from_settings,
    apparel_uses_product_variant_engine,
    apparel_workspace_contract,
)

ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase316_apparel_contract_is_standalone_ui_backed_by_item_variants():
    contract = apparel_workspace_contract()
    assert APPAREL_PAGE_ID == "apparel"
    assert APPAREL_SETTINGS_KEY == "apparel/enabled"
    assert APPAREL_ENGINE_BACKING == "product_variants"
    assert apparel_uses_product_variant_engine() is True
    assert contract["page_id"] == "apparel"
    assert contract["variant_scope"] == "variant"
    assert "color" in contract["visible_columns"]
    assert "size" in contract["visible_columns"]
    assert "barcode" in contract["visible_columns"]
    assert "apparel_gateway.py" in contract["forbidden_engine_files"]


def test_phase316_apparel_visibility_comes_from_apparel_enabled():
    assert apparel_page_enabled_from_settings({"apparel/enabled": "true"}) is True
    assert apparel_page_enabled_from_settings({"apparel/enabled": "false"}) is False
    assert apparel_page_enabled_from_settings({"apparel": {"enabled": True}}) is True
    assert apparel_page_enabled_from_settings({"apparel": {"enabled": False}}) is False


def test_phase316_main_window_registers_apparel_as_top_level_inventory_page():
    main_window = text("alrajhi_client/views/main_window.py")
    policy = text("alrajhi_client/workspace/navigation/module_visibility_policy.py")
    settings_widget = text("alrajhi_client/views/widgets/settings_widget.py")
    settings_tabs = text("alrajhi_client/features/settings/settings_document_tabs.py")
    i18n = text("alrajhi_client/i18n/translator.py")

    assert "\'apparel\': (\'alrajhi_client.views.apparel\', \'ApparelWorkspaceWidget\')" in main_window
    assert "'apparel': ('apparel.workspace_title', 'nav_apparel')" in main_window
    assert "('apparel', ApparelWorkspaceWidget)" in main_window
    assert "translate('apparel.workspace_title')" in main_window
    assert "page_enabled('apparel')" in main_window
    assert "'apparel': (('apparel/enabled', True),)" in policy
    assert "contract_apparel_enabled" in settings_widget
    assert "'apparel/enabled': self.contract_apparel_enabled.isChecked()" in settings_widget
    assert "class ApparelSettingsTab" in settings_tabs
    assert "'apparel': ApparelSettingsTab" in settings_tabs
    assert "'nav_apparel': 'الألبسة'" in i18n


def test_phase316_apparel_workspace_uses_product_service_not_direct_data_access():
    widget = text("alrajhi_client/views/apparel/apparel_workspace_widget.py")
    assert "class ApparelWorkspaceWidget(QWidget)" in widget
    assert "from core.services.product_service import product_service" in widget
    assert "product_service.items" in widget
    assert "product_service.item_variants" in widget
    assert "product_service.item_by_barcode" in widget
    assert "barcode_scope" in widget
    assert "matched_variant" in widget
    forbidden = ["database.dao", "database.repositories", "DatabaseConnection", ".execute(", "SELECT "]
    for marker in forbidden:
        assert marker not in widget


def test_phase316_document_contract_and_permissions_alias_to_materials_engine():
    document_contract = text("alrajhi_client/workspace/documents/document_contract.py")
    permission_binder = text("alrajhi_client/workspace/documents/document_permission_binder.py")
    assert 'document_type="apparel"' in document_contract
    assert 'gateway="product_gateway"' in document_contract
    assert 'api_resource="/api/items"' in document_contract
    assert 'document_class="views.apparel.apparel_workspace_widget.ApparelWorkspaceWidget"' in document_contract
    assert 'view="apparel.view"' in document_contract
    assert 'create="apparel.variant"' in document_contract
    assert '"apparel.view": "edit_items"' in permission_binder
    assert '"apparel.variant": "edit_items"' in permission_binder


def test_phase316_no_independent_apparel_engine_files_were_added():
    forbidden_names = {"apparel_gateway.py", "apparel_repository.py", "apparel_dao.py", "apparel_payment_service.py"}
    found = {path.name for path in ROOT.rglob("*.py") if path.name in forbidden_names}
    assert not found


def test_phase316_release_gate_registered_and_documented():
    gate = text("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(316, "APPAREL_WORKSPACE_SHELL")' in gate
    assert '(316, "apparel_workspace_shell")' in gate
    assert "tests/test_phase316_apparel_workspace_shell.py" in gate
    assert (ROOT / "PHASE316_APPAREL_WORKSPACE_SHELL.md").exists()
