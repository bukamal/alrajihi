# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_material_shell_contract_declares_api_network_currency_and_barcode():
    text = _read('alrajhi_client/features/items/material_shell_contract.py')
    assert 'MATERIAL_DOCUMENT_TYPE = "material"' in text
    assert 'MATERIAL_API_RESOURCE = "/api/items"' in text
    assert 'MATERIAL_REMOTE_GATEWAY = "gateways.remote.product_gateway.RemoteItemGateway"' in text
    assert 'MATERIAL_UNIT_PERSISTENCE_POLICY' in text
    assert 'CURRENCY_DISPLAY' in text
    assert 'NETWORK_REMOTE_AVAILABLE' in text
    assert 'assert_material_shell_contract' in text


def test_material_document_uses_material_descriptor_not_legacy_item_descriptor():
    text = _read('alrajhi_client/features/items/item_editor_tab.py')
    assert 'super().__init__(MATERIAL_DOCUMENT_TYPE' in text
    assert 'DOCUMENT_DESCRIPTOR = material_descriptor()' in text
    assert 'self.document_descriptor = self.DOCUMENT_DESCRIPTOR' in text
    assert 'DocumentPermissionBinder(self.document_descriptor)' in text
    assert "setProperty('document_api_resource'" in text
    assert 'shell_contract_matrix' in text


def test_material_document_keeps_responsive_splitter_and_shell_component_name():
    text = _read('alrajhi_client/features/items/item_editor_tab.py')
    assert 'QSplitter' in text
    assert 'ItemEditorResponsiveSplitter' in text
    assert "setProperty('shell_component', 'material.master_detail_splitter')" in text
    assert 'setStretchFactor' in text


def test_material_document_binds_permissions_to_save_print_and_barcode_actions():
    text = _read('alrajhi_client/features/items/item_editor_tab.py')
    assert "can_document_action('save')" in text
    assert "can_document_action('print')" in text
    assert 'self.permission_denied_message' in text
    assert 'material_shell_permission_binding' in text
    assert 'self.apply_document_permissions()' in text


def test_material_workspace_list_uses_same_descriptor_and_permission_binder():
    text = _read('alrajhi_client/views/widgets/items_widget.py')
    assert 'material_shell_contract()' in text
    assert 'self.document_descriptor = self.material_shell_contract.descriptor' in text
    assert 'DocumentPermissionBinder(self.document_descriptor)' in text
    assert 'can_material_action' in text
    assert "can_material_action('print')" in text
    assert "can_material_action('delete'" in text


def test_material_shell_i18n_badge_exists_for_three_languages():
    text = _read('alrajhi_client/i18n/translator.py')
    assert text.count("'material_shell_badge'") >= 3
    assert 'Document Shell · API' in text
    assert 'Rechte' in text
    assert 'صلاحيات' in text


def test_material_service_and_gateway_keep_remote_atomic_unit_policy():
    service = _read('alrajhi_client/core/services/product_service.py')
    remote = _read('alrajhi_client/gateways/remote/product_gateway.py')
    assert 'item_gateway.is_remote()' in service
    assert 'Remote item units are saved atomically through item create/update payloads' in remote
    assert 'replace_units' in service
    assert 'get_item_by_barcode' in remote
