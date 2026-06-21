from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_restaurant_dashboard_uses_fullscreen_stacked_operational_pages():
    source = read("alrajhi_client/views/restaurant/restaurant_dashboard.py")
    assert "restaurantFullscreenModeStack" in source
    assert "restaurantOrderModePage" in source
    assert "restaurantKitchenModePage" in source
    assert "restaurantTablesModePage" in source
    assert "RESTAURANT_FULLSCREEN_ORDER_SIZES" in source
    assert "RESTAURANT_FULLSCREEN_KITCHEN_SIZES" in source
    assert "show_tables_mode" in source
    assert "Phase 298 no longer" in source


def test_kitchen_page_does_not_require_order_and_kds_and_tables_as_three_major_panes():
    source = read("alrajhi_client/views/restaurant/restaurant_dashboard.py")
    assert "self.workspace_stack.setCurrentWidget(self.kitchen_page)" in source
    assert "self.kitchen_table_map.setVisible(False)" in source
    assert "self.kitchen_splitter.setStretchFactor(0, 7)" in source
    assert "self.kitchen_splitter.setStretchFactor(1, 2)" in source


def test_restaurant_money_closure_formats_menu_cards_and_summary():
    pos = read("alrajhi_client/views/restaurant/restaurant_pos_widget.py")
    table_map = read("alrajhi_client/views/restaurant/table_map_widget.py")
    model = read("alrajhi_client/features/restaurant/restaurant_order_model.py")
    assert "price_label = _display_money(price)" in pos
    assert "currency.format_display_amount(currency.to_display" in pos
    assert "currency.format_display_amount(currency.to_display" in table_map
    assert "policy_for(currency_code=self.display_currency).format_money" in model


def test_restaurant_fullscreen_styles_and_translations_exist():
    qss = read("alrajhi_client/theme/qss.py")
    tr = read("alrajhi_client/i18n/translator.py")
    assert "restaurantFullscreenModeStack" in qss
    assert "restaurantKitchenFullscreenSplitter" in qss
    assert "restaurant.mode.tables" in tr
    assert "الطاولات" in tr
    assert "Tische" in tr
    assert "Tables" in tr
