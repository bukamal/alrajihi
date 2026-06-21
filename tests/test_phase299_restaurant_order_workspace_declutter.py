from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_phase299_order_mode_uses_full_pos_workspace_not_split_table_map():
    dashboard = read('alrajhi_client/views/restaurant/restaurant_dashboard.py')
    assert 'Phase 299 makes the current order a full workspace' in dashboard
    assert 'order_page_layout.addWidget(self.pos, 1)' in dashboard
    assert 'self.table_map.setVisible(False)' in dashboard
    assert 'self.splitter.setVisible(False)' in dashboard


def test_phase299_order_money_strip_is_three_decisive_values_only():
    pos = read('alrajhi_client/views/restaurant/restaurant_pos_widget.py')
    assert 'Phase 299: permanent bill strip shows only decisive operator values' in pos
    assert '("total", "restaurant.current_total")' in pos
    assert '("paid", "restaurant.paid")' in pos
    assert '("remaining", "restaurant.remaining")' in pos
    assert '("subtotal", "restaurant.subtotal")' not in pos


def test_phase299_primary_actions_are_not_three_large_group_cards():
    pos = read('alrajhi_client/views/restaurant/restaurant_pos_widget.py')
    assert 'restaurantMoreActionsButton' in pos
    assert 'self.more_actions_menu' in pos
    assert 'self._restaurant_menu_actions' in pos
    assert 'for button in (self.send_kitchen_btn, self.payment_btn, self.close_btn)' in pos


def test_phase299_order_grid_and_menu_are_operator_dense():
    pos = read('alrajhi_client/views/restaurant/restaurant_pos_widget.py')
    assert 'self.lines.apply_visible_keys(["row", "item", "qty", "price", "total"])' in pos
    assert 'button.setMinimumSize(132, 70)' in pos
    assert 'self.menu_scroll.setMaximumHeight(190)' in pos
