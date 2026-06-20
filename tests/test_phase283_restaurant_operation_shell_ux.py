from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def test_restaurant_dashboard_uses_operation_modes_not_permanent_four_panes():
    source = _read('alrajhi_client/views/restaurant/restaurant_dashboard.py')
    assert 'restaurant.operation_shell' in source
    assert 'QStackedWidget' in source
    assert 'restaurantSideModeStack' in source
    assert 'show_order_mode' in source
    assert 'show_kitchen_mode' in source
    assert 'show_analytics_mode' in source
    assert 'show_analytics_panel' in source
    assert 'self.splitter.setStretchFactor(1, 6)' in source


def test_restaurant_pos_prioritizes_order_grid_over_menu_cards():
    source = _read('alrajhi_client/views/restaurant/restaurant_pos_widget.py')
    assert source.index('self.lines = RestaurantOrderGrid') < source.index('self.menu_scroll = QScrollArea')
    assert 'restaurantPrimaryActions' in source
    assert 'restaurantMenuSectionTitle' in source
    assert 'setObjectName("restaurantPaymentButton")' in source


def test_restaurant_table_map_has_semantic_service_statuses_and_money():
    source = _read('alrajhi_client/views/restaurant/table_map_widget.py')
    assert 'restaurant_status", self._ui_status(table)' in source
    assert '"kitchen"' in source
    assert '"ready"' in source
    assert 'restaurant.table_total' in source
    assert 'currency.format_display_amount' in source


def test_restaurant_settings_expose_operation_screen_visibility_controls():
    settings_service = _read('alrajhi_client/core/services/settings_service.py')
    settings_tabs = _read('alrajhi_client/features/settings/settings_document_tabs.py')
    for key in ('restaurant/ui/show_kitchen_panel', 'restaurant/ui/show_analytics_panel', 'restaurant/ui/table_card_density'):
        assert key in settings_service
        assert key in settings_tabs


def test_restaurant_operation_shell_translations_and_styles_exist():
    tr = _read('alrajhi_client/i18n/translator.py')
    qss = _read('alrajhi_client/theme/qss.py')
    for key in ('restaurant.operation_shell', 'restaurant.mode.order', 'restaurant.mode.kitchen', 'restaurant.status.kitchen', 'restaurant.status.ready'):
        assert key in tr
    assert 'restaurantTableButton[restaurant_status="kitchen"]' in qss
    assert 'restaurantTableButton[restaurant_status="ready"]' in qss
    assert 'restaurantOrderModeButton[active="true"]' in qss
