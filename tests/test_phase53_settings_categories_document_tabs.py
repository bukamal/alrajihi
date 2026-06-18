from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_settings_sections_are_document_tabs_and_service_bound():
    source = (ROOT / 'alrajhi_client/features/settings/settings_document_tabs.py').read_text(encoding='utf-8')
    assert 'class SettingsSectionDocumentTab(BaseDocumentTab)' in source
    for name in ('CompanySettingsTab', 'AccountingSettingsTab', 'InventorySettingsTab', 'RestaurantSettingsTab', 'PrintingSettingsTab', 'UISettingsTab', 'SecuritySettingsTab'):
        assert name in source
    assert 'settings_service.set' in source
    assert 'settings_service.clear_cache' in source
    assert 'DatabaseConnection' not in source
    assert '.execute(' not in source


def test_settings_sections_are_registered_in_workspace_quick_open():
    source = (ROOT / 'alrajhi_client/views/main_window.py').read_text(encoding='utf-8')
    assert 'def open_settings_section_document' in source
    assert 'from features.settings import SETTINGS_SECTION_TABS' in source
    assert "settings:{section}" in source
    assert "item.key.startswith('settings:')" in source


def test_category_editor_is_decomposed_into_panels():
    source = (ROOT / 'alrajhi_client/features/categories/category_editor_tab.py').read_text(encoding='utf-8')
    panels = (ROOT / 'alrajhi_client/features/categories/components/category_panels.py').read_text(encoding='utf-8')
    assert 'CategoryHeaderPanel' in source
    assert 'CategoryPropertiesPanel' in source
    assert 'class CategoryHeaderPanel' in panels
    assert 'class CategoryPropertiesPanel' in panels
    assert 'product_service.add_category' in source
    assert 'product_service.update_category' in source
