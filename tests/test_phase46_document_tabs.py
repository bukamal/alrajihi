from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_document_tab_foundation_exists():
    assert (ROOT / 'alrajhi_client/workspace/documents/base_document_tab.py').exists()
    assert (ROOT / 'alrajhi_client/features/items/item_editor_tab.py').exists()
    assert (ROOT / 'alrajhi_client/features/categories/category_editor_tab.py').exists()


def test_main_window_routes_quick_item_to_document_tab():
    text = (ROOT / 'alrajhi_client/views/main_window.py').read_text(encoding='utf-8')
    assert 'def open_item_document' in text
    assert 'def open_category_document' in text
    assert 'ItemEditorTab' in text
    # Phase378/458: category creation is routed inline through CategoriesWidget,
    # not instantiated eagerly in MainWindow.
    categories = (ROOT / 'alrajhi_client/views/widgets/categories_widget.py').read_text(encoding='utf-8')
    assert 'CategoryEditorTab' in categories
    assert "_open_page_inline_action('categories'" in text


def test_list_widgets_route_add_edit_to_document_tabs():
    items = (ROOT / 'alrajhi_client/views/widgets/items_widget.py').read_text(encoding='utf-8')
    categories = (ROOT / 'alrajhi_client/views/widgets/categories_widget.py').read_text(encoding='utf-8')
    assert 'main.open_item_document' in items
    assert 'main.open_category_document' in categories
