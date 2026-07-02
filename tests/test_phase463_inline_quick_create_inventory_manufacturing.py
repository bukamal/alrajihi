from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'alrajhi_client' / 'ui' / 'inline_quick_create_registry.py'
PANEL = ROOT / 'alrajhi_client' / 'ui' / 'inline_quick_create.py'
INVENTORY_TRANSFER = ROOT / 'alrajhi_client' / 'features' / 'inventory' / 'documents' / 'inventory_transfer_document_tab.py'
BOM = ROOT / 'alrajhi_client' / 'features' / 'manufacturing' / 'bom_document_tab.py'
PRODUCTION = ROOT / 'alrajhi_client' / 'features' / 'manufacturing' / 'production_order_document_tab.py'
TRANSLATOR = ROOT / 'alrajhi_client' / 'i18n' / 'translator.py'


def test_phase463_registry_and_panel_add_warehouse_with_official_services():
    registry = REGISTRY.read_text(encoding='utf-8')
    panel = PANEL.read_text(encoding='utf-8')
    assert '"warehouse": QuickCreateDefinition' in registry
    assert 'permission_operation="warehouse_create"' in registry
    assert 'inventory_operation_policy.OP_WAREHOUSE_CREATE' in panel
    assert 'warehouse_service.add_warehouse(payload)' in panel
    assert '_find_existing_warehouse' in panel
    assert '_save_warehouse' in panel
    assert 'item_type = self.context.get("item_type") or STOCK' in panel
    assert 'QDialog' not in panel
    assert 'exec(' not in panel and 'exec_(' not in panel


def test_phase463_inventory_transfer_has_inline_warehouse_and_item_create():
    source = INVENTORY_TRANSFER.read_text(encoding='utf-8')
    assert "InlineQuickCreatePanel('warehouse'" in source
    assert "InlineQuickCreatePanel('item'" in source
    assert 'InventoryTransferInlineQuickFromWarehouseButton' in source
    assert 'InventoryTransferInlineQuickToWarehouseButton' in source
    assert 'InventoryTransferInlineQuickWarehousePanel' in source
    assert 'InventoryTransferInlineQuickItemPanel' in source
    assert '_on_inline_warehouse_created' in source
    assert '_on_inline_item_created' in source
    assert '_load_warehouses(target_id=target_id' in source
    assert 'addLayout(lookup_box' in source
    assert 'QDialog' not in source


def test_phase463_bom_uses_inline_finished_product_and_component_create():
    source = BOM.read_text(encoding='utf-8')
    assert "InlineQuickCreatePanel('item', self, context={'item_type': FINISHED_PRODUCT})" in source
    assert "InlineQuickCreatePanel('item', self)" in source
    assert 'BomInlineQuickProductButton' in source
    assert 'BomInlineQuickComponentButton' in source
    assert 'BomInlineQuickProductPanel' in source
    assert 'BomInlineQuickComponentPanel' in source
    assert '_on_inline_product_created' in source
    assert '_on_inline_component_created' in source
    assert '_load_products()' in source
    assert 'QDialog' not in source


def test_phase463_production_order_uses_inline_product_and_warehouse_create():
    source = PRODUCTION.read_text(encoding='utf-8')
    assert "InlineQuickCreatePanel('item', self, context={'item_type': FINISHED_PRODUCT})" in source
    assert "InlineQuickCreatePanel('warehouse'" in source
    assert 'ProductionOrderInlineQuickProductButton' in source
    assert 'ProductionOrderInlineQuickRawWarehouseButton' in source
    assert 'ProductionOrderInlineQuickOutputWarehouseButton' in source
    assert 'ProductionOrderInlineQuickProductPanel' in source
    assert 'ProductionOrderInlineQuickWarehousePanel' in source
    assert '_on_inline_product_created' in source
    assert '_on_inline_warehouse_created' in source
    assert '_load_warehouses(target_id=target_id' in source
    assert 'QDialog' not in source


def test_phase463_inventory_manufacturing_inline_translations_exist_for_supported_languages():
    source = TRANSLATOR.read_text(encoding='utf-8')
    for key in (
        'inline_quick_create_warehouse_tooltip',
        'inline_quick_create_inventory_item_tooltip',
        'inline_quick_create_finished_product_tooltip',
        'inline_quick_create_component_item_tooltip',
        'inline_quick_create_warehouse_title',
        'inline_quick_create_warehouse_subtitle',
        'inline_quick_create_item_created_search_to_add',
    ):
        assert source.count(key) >= 4
