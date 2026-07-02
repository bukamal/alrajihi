from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ITEM_EDITOR = ROOT / 'alrajhi_client' / 'features' / 'items' / 'item_editor_tab.py'
TRANSLATOR = ROOT / 'alrajhi_client' / 'i18n' / 'translator.py'
LEGACY_ITEM_DIALOG = ROOT / 'alrajhi_client' / 'views' / 'dialogs' / 'item_dialog.py'


def test_material_new_form_does_not_seed_default_subunit_box():
    source = ITEM_EDITOR.read_text(encoding='utf-8')
    prepare = source.split('def _prepare_new_material', 1)[1].split('def reload_categories', 1)[0]
    clear = source.split('def clear_for_new', 1)[1].split('def generate_barcode', 1)[0]
    assert "add_unit_row(tr('unit_box')" not in prepare
    assert "add_unit_row(tr('unit_box')" not in clear
    assert "'علبة', 1" not in prepare
    assert "'علبة', 1" not in clear
    assert 'sub-units are explicit user decisions' in source


def test_material_editor_has_inline_quick_category_creation_contract():
    source = ITEM_EDITOR.read_text(encoding='utf-8')
    assert 'MaterialQuickAddCategoryButton' in source
    assert 'create_category_from_material_editor' in source
    assert "InlineQuickCreatePanel('category'" in source
    assert "self.reload_categories(select_id=result.get('id'))" in source
    assert 'InlineQuickCreatePanel' in source
    assert 'category_operation_policy.can(category_operation_policy.OP_CREATE)' in source


def test_material_quick_category_translations_exist_for_supported_languages():
    source = TRANSLATOR.read_text(encoding='utf-8')
    for lang in ('ar', 'de', 'en', 'fr'):
        assert f"'{lang}':" in source
    for key in (
        'material_quick_add_category',
        'material_quick_add_category_tooltip',
        'material_quick_add_category_denied',
        'material_quick_category_title',
        'material_quick_category_subtitle',
        'material_category_already_exists_selected',
        'material_no_default_subunit_contract',
    ):
        assert source.count(key) >= 4


def test_legacy_item_dialog_uses_modern_quick_category_dialog_too():
    source = LEGACY_ITEM_DIALOG.read_text(encoding='utf-8')
    assert 'QInputDialog' not in source
    assert 'MaterialDialogQuickCategoryDialog' not in source
    assert "InlineQuickCreatePanel('category'" in source
    assert 'category_operation_policy.can(category_operation_policy.OP_CREATE)' in source
    assert "self.refresh_categories(select_id=result.get('id'))" in source
