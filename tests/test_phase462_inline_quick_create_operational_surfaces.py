from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / 'alrajhi_client' / 'ui' / 'inline_quick_create.py'
POS = ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'pos_widget.py'
RESTAURANT_SIMPLE = ROOT / 'alrajhi_client' / 'views' / 'restaurant' / 'restaurant_simple_pos_widget.py'
RESTAURANT_DASHBOARD = ROOT / 'alrajhi_client' / 'views' / 'restaurant' / 'restaurant_dashboard.py'
CAFE = ROOT / 'alrajhi_client' / 'views' / 'cafe' / 'cafe_workspace_widget.py'
TRANSLATOR = ROOT / 'alrajhi_client' / 'i18n' / 'translator.py'


def test_phase462_pos_uses_inline_quick_create_without_material_cards_or_dialogs():
    source = POS.read_text(encoding='utf-8')
    assert "InlineQuickCreatePanel('cashbox'" in source
    assert "InlineQuickCreatePanel('item'" in source
    assert 'POSInlineQuickCashboxButton' in source
    assert 'POSInlineQuickCashboxPanel' in source
    assert 'POSInlineQuickItemButton' in source
    assert 'POSInlineQuickItemPanel' in source
    assert '_on_inline_cashbox_created' in source
    assert '_on_inline_item_created' in source
    assert 'pos_service.new_cart' in source
    assert 'add_barcode_to_cart(barcode, mode=' in source
    # POS remains table-first; quick create is a collapsible panel, not a product-card surface.
    assert 'OperationalItemCardGrid(' not in source


def test_phase462_restaurant_simple_has_inline_category_and_item_create():
    source = RESTAURANT_SIMPLE.read_text(encoding='utf-8')
    assert "InlineQuickCreatePanel('category'" in source
    assert "InlineQuickCreatePanel('item'" in source
    assert 'restaurantSimpleInlineQuickCategoryButton' in source
    assert 'restaurantSimpleInlineQuickCategoryPanel' in source
    assert 'restaurantSimpleInlineQuickItemButton' in source
    assert 'restaurantSimpleInlineQuickItemPanel' in source
    assert '_on_inline_category_created' in source
    assert '_on_inline_item_created' in source
    assert 'self.reload_categories()' in source
    assert 'self.reload_menu()' in source
    assert 'set_context(categories=self.categories)' in source


def test_phase462_restaurant_dashboard_and_cafe_share_operational_inline_create():
    source = RESTAURANT_DASHBOARD.read_text(encoding='utf-8')
    cafe_source = CAFE.read_text(encoding='utf-8')
    assert "InlineQuickCreatePanel('category'" in source
    assert "InlineQuickCreatePanel('item'" in source
    assert 'restaurantDashboardInlineQuickCategoryButton' in source
    assert 'restaurantDashboardInlineQuickItemButton' in source
    assert 'restaurantDashboardInlineQuickCategoryPanel' in source
    assert 'restaurantDashboardInlineQuickItemPanel' in source
    assert 'self.pos.reload_menu()' in source
    # Cafe inherits the same dashboard surface instead of growing a separate ad-hoc implementation.
    assert 'class CafeWorkspaceWidget(RestaurantDashboard)' in cafe_source
    assert 'QDialog' not in cafe_source


def test_phase462_inline_item_result_carries_context_for_operational_refresh():
    source = PANEL.read_text(encoding='utf-8')
    assert '"category_id": payload.get("category_id")' in source
    assert '"unit": payload.get("unit")' in source
    assert 'product_service.add_item(payload)' in source
    assert 'QDialog' not in source
    assert 'exec(' not in source and 'exec_(' not in source


def test_phase462_operational_inline_translations_exist_for_supported_languages():
    source = TRANSLATOR.read_text(encoding='utf-8')
    for key in (
        'inline_quick_create_pos_item_tooltip',
        'inline_quick_create_restaurant_category_tooltip',
        'inline_quick_create_restaurant_item_tooltip',
        'inline_quick_create_item_created_scan_or_search',
        'inline_quick_create_item_created_available',
        'inline_quick_create_cashbox_created_select_after_clear',
    ):
        assert source.count(key) >= 4
