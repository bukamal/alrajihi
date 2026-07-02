from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_phase467_floating_quick_create_host_is_central_and_layout_safe():
    helper = read('alrajhi_client/ui/floating_quick_create.py')
    panel = read('alrajhi_client/ui/inline_quick_create.py')
    assert 'def floating_surface_for(entity_type: str) -> str:' in helper
    assert 'def show_floating_quick_create(panel: QWidget' in helper
    assert 'def position_floating_quick_create(panel: QWidget' in helper
    assert 'quickCreateSurface' in panel
    assert 'floatingQuickCreate' in panel
    assert 'show_floating_quick_create(self' in panel
    assert 'hide_floating_quick_create(self)' in panel
    assert 'FloatingQuickCreate' in helper
    assert 'QDialog' not in panel
    assert 'QInputDialog' not in panel


def test_phase467_registry_drives_popover_and_drawer_surfaces():
    helper = read('alrajhi_client/ui/floating_quick_create.py')
    registry = read('alrajhi_client/ui/inline_quick_create_registry.py')
    assert 'definition_for(entity_type).mode' in helper
    assert 'return "floating_drawer"' in helper
    assert 'return "floating_popover"' in helper
    for entity in ('category', 'unit', 'customer', 'supplier', 'item', 'cashbox', 'bank_account', 'warehouse'):
        assert f'"{entity}": QuickCreateDefinition' in registry


def test_phase467_material_and_document_surfaces_do_not_insert_quick_create_into_layouts():
    files = [
        'alrajhi_client/features/items/item_editor_tab.py',
        'alrajhi_client/views/dialogs/item_dialog.py',
        'alrajhi_client/features/transactions/transaction_document_tab.py',
        'alrajhi_client/features/vouchers/components/voucher_link.py',
        'alrajhi_client/features/vouchers/components/voucher_payment.py',
    ]
    for rel in files:
        source = read(rel)
        assert 'InlineQuickCreatePanel' in source
        assert 'addRow(\'\', self.quick_category_panel)' not in source
        assert 'root.addWidget(self.quick_party_panel)' not in source
        assert 'root.addWidget(self.quick_item_panel)' not in source
        assert 'layout.addWidget(self.quick_customer_panel' not in source
        assert 'layout.addWidget(self.quick_supplier_panel' not in source
        assert 'layout.addWidget(self.quick_cashbox_panel' not in source
        assert 'layout.addWidget(self.quick_bank_panel' not in source
        assert 'Phase467' in source


def test_phase467_operational_inventory_manufacturing_surfaces_are_floating_not_inline_stacks():
    files = [
        'alrajhi_client/views/restaurant/restaurant_dashboard.py',
        'alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py',
        'alrajhi_client/features/inventory/documents/inventory_transfer_document_tab.py',
        'alrajhi_client/features/manufacturing/bom_document_tab.py',
        'alrajhi_client/features/manufacturing/production_order_document_tab.py',
    ]
    for rel in files:
        source = read(rel)
        assert 'InlineQuickCreatePanel' in source
        assert 'addWidget(self.inline_category_panel)' not in source
        assert 'addWidget(self.inline_item_panel)' not in source
        assert 'addWidget(self.inline_warehouse_panel)' not in source
        assert 'addWidget(self.inline_product_panel)' not in source
        assert 'addWidget(self.inline_component_panel)' not in source
        assert 'Phase467' in source


def test_phase467_pos_uses_floating_host_without_pushing_scan_bar():
    pos = read('alrajhi_client/views/widgets/pos_widget.py')
    assert 'POSQuickCreateDrawer_cashbox' in pos
    assert 'POSQuickCreateDrawer_item' in pos
    assert 'quickCreateSurface", "floating_drawer"' in pos
    assert 'panel.show_panel(anchor=self.sender())' in pos
    assert 'mapFromGlobal(self.mapToGlobal(QPoint(x, scan_bottom)))' in pos
    assert 'layout.addWidget(self.inline_cashbox_panel)' not in pos
    assert 'layout.addWidget(self.inline_item_panel)' not in pos
