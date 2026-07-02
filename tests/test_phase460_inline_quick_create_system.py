from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'alrajhi_client' / 'ui' / 'inline_quick_create_registry.py'
PANEL = ROOT / 'alrajhi_client' / 'ui' / 'inline_quick_create.py'
ITEM_EDITOR = ROOT / 'alrajhi_client' / 'features' / 'items' / 'item_editor_tab.py'
LEGACY_ITEM_DIALOG = ROOT / 'alrajhi_client' / 'views' / 'dialogs' / 'item_dialog.py'
TRANSACTION_TAB = ROOT / 'alrajhi_client' / 'features' / 'transactions' / 'transaction_document_tab.py'
TRANSLATOR = ROOT / 'alrajhi_client' / 'i18n' / 'translator.py'


def test_inline_quick_create_registry_is_central_and_covers_core_entities():
    source = REGISTRY.read_text(encoding='utf-8')
    for entity in ('category', 'unit', 'customer', 'supplier', 'item'):
        assert f'"{entity}": QuickCreateDefinition' in source
    assert 'network_boundary: str = "official_service_gateway"' in source
    assert 'duplicate_policy: str = "select_existing"' in source
    assert 'supported_entities' in source


def test_inline_quick_create_panel_is_inline_first_not_dialog_or_tab():
    source = PANEL.read_text(encoding='utf-8')
    assert 'class InlineQuickCreatePanel(QFrame)' in source
    assert 'QDialog' not in source
    assert 'exec(' not in source and 'exec_(' not in source
    assert 'open_' not in source or 'open_category_document' not in source
    assert 'created = pyqtSignal(str, dict)' in source
    assert 'quick_create_can' in source
    assert 'entity_service.add_customer' in source
    assert 'entity_service.add_supplier' in source
    assert 'product_service.add_category' in source
    assert 'product_service.add_item' in source


def test_material_forms_use_unified_inline_category_panel():
    source = ITEM_EDITOR.read_text(encoding='utf-8')
    legacy = LEGACY_ITEM_DIALOG.read_text(encoding='utf-8')
    for text in (source, legacy):
        assert "InlineQuickCreatePanel('category'" in text
        assert 'MaterialQuickCategoryDialog' not in text
        assert 'MaterialDialogQuickCategoryDialog' not in text
        assert 'QInputDialog' not in text
    assert '_on_inline_category_created' in source
    assert '_on_inline_category_created' in legacy


def test_transaction_documents_have_inline_quick_party_and_item_creation():
    source = TRANSACTION_TAB.read_text(encoding='utf-8')
    assert 'TransactionInlineQuickPartyButton' in source
    assert 'TransactionInlineQuickPartyPanel' in source
    assert 'TransactionInlineQuickItemButton' in source
    assert 'TransactionInlineQuickItemPanel' in source
    assert 'InlineQuickCreatePanel(self._quick_party_entity()' in source
    assert "InlineQuickCreatePanel('item'" in source
    assert '_on_inline_party_created' in source
    assert '_on_inline_item_created' in source
    assert 'self._load_parties()' in source
    assert 'self.add_item_from_search()' in source


def test_inline_quick_create_translations_exist_for_supported_languages():
    source = TRANSLATOR.read_text(encoding='utf-8')
    for key in (
        'inline_quick_create_save_select',
        'inline_quick_create_permission_denied',
        'inline_quick_create_party_tooltip',
        'inline_quick_create_item_tooltip',
        'inline_quick_create_customer_title',
        'inline_quick_create_supplier_title',
        'inline_quick_create_item_title',
        'inline_quick_create_category_title',
        'inline_quick_create_unit_title',
    ):
        assert source.count(key) >= 4
