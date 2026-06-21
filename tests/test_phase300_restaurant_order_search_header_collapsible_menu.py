from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase300_search_moved_to_header_and_menu_is_collapsible():
    pos = (ROOT / "alrajhi_client/views/restaurant/restaurant_pos_widget.py").read_text(encoding="utf-8")
    assert 'restaurantOrderHeaderSearch' in pos
    assert 'restaurantOrderSearchHeader' in pos
    assert 'restaurantHeaderManualItemButton' in pos
    assert 'restaurantMenuToggleButton' in pos
    assert 'self.menu_scroll.setVisible(False)' in pos
    assert 'self.menu_toggle_btn.toggled.connect(self._set_menu_panel_visible)' in pos
    assert 'root.addLayout(menu_header)' not in pos


def test_phase300_table_keeps_only_decisive_columns_visible_by_default():
    schema = (ROOT / "alrajhi_client/features/restaurant/restaurant_order_schema.py").read_text(encoding="utf-8")
    assert 'TransactionColumn("modifiers", "restaurant_column_modifiers", False, False, False' in schema
    assert 'TransactionColumn("unit", "transaction_column_unit", False, False, True' in schema
    assert 'TransactionColumn("status", "restaurant_column_status", False, False, True' in schema
    assert 'TransactionColumn("notes", "transaction_column_notes", False, False, False' in schema
    assert 'TransactionColumn("item", "transaction_column_item", True, True, True' in schema
    assert 'TransactionColumn("qty", "transaction_column_qty", True, True, True' in schema
    assert 'TransactionColumn("total", "transaction_column_total", True, True, True' in schema


def test_phase300_qss_supports_header_search_and_collapsible_menu():
    qss = (ROOT / "alrajhi_client/theme/qss.py").read_text(encoding="utf-8")
    assert 'QFrame#restaurantOrderSearchHeader {{' in qss
    assert 'QLineEdit#restaurantOrderHeaderSearch {{' in qss
    assert 'QFrame#restaurantMenuToggleCard {{' in qss
    assert 'QToolButton#restaurantMenuToggleButton {{' in qss
    assert 'QToolButton#restaurantMenuToggleButton:checked {{' in qss
