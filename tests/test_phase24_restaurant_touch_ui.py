from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_restaurant_touch_ui_qss_status_cards_present():
    qss = (ROOT / 'alrajhi_client' / 'theme' / 'qss.py').read_text(encoding='utf-8')
    assert 'Phase 24: modern restaurant touch UI' in qss
    assert 'QPushButton#restaurantTableButton[restaurant_status="free"]' in qss
    assert 'QPushButton#restaurantTableButton[restaurant_status="occupied"]' in qss
    assert 'QPushButton#restaurantTableButton[restaurant_status="payment"]' in qss
    assert 'QPushButton#restaurantTableButton[restaurant_status="reserved"]' in qss


def test_restaurant_widgets_have_touch_object_names_and_icons():
    table_map = (ROOT / 'alrajhi_client' / 'views' / 'restaurant' / 'table_map_widget.py').read_text(encoding='utf-8')
    pos = (ROOT / 'alrajhi_client' / 'views' / 'restaurant' / 'restaurant_pos_widget.py').read_text(encoding='utf-8')
    dashboard = (ROOT / 'alrajhi_client' / 'views' / 'restaurant' / 'restaurant_dashboard.py').read_text(encoding='utf-8')
    assert 'setObjectName("restaurantTableButton")' in table_map
    assert 'setMinimumSize(178, 128)' in table_map
    assert 'setCursor(Qt.PointingHandCursor)' in table_map
    assert '🍽' in table_map
    assert 'setObjectName("restaurantKitchenButton")' in pos
    assert 'setObjectName("restaurantPaymentButton")' in pos
    assert 'setMinimumHeight(66)' in pos
    assert 'setLayoutDirection(qt_layout_direction())' in dashboard


def test_restaurant_touch_translations_exist_for_three_languages():
    translator = (ROOT / 'alrajhi_client' / 'i18n' / 'translator.py').read_text(encoding='utf-8')
    assert "'restaurant.touch_mode': 'وضع لمس المطاعم'" in translator
    assert "'restaurant.touch_mode': 'Restaurant-Touchmodus'" in translator
    assert "'restaurant.touch_mode': 'Restaurant touch mode'" in translator
