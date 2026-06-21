from alrajhi_client.theme.brand import get_tokens
from alrajhi_client.theme.qss import build_global_qss


def test_phase297_restaurant_qss_builds_for_light_and_dark_themes():
    for theme in ("light", "dark"):
        qss = build_global_qss(get_tokens(theme))
        assert "restaurantTableOperationsMenuButton" in qss
        assert "restaurant_compact_mode=\"true\"" in qss
        assert "restaurant_layout_mode=\"compact\"" in qss
        assert "background-color:" in qss


def test_phase297_restaurant_qss_source_escapes_new_css_blocks():
    qss = open("alrajhi_client/theme/qss.py", "r", encoding="utf-8").read()
    assert 'QToolButton#restaurantTableOperationsMenuButton {{' in qss
    assert 'QSplitter#restaurantOperationSplitter[restaurant_layout_mode="compact"]::handle {{' in qss
    assert 'QWidget#restaurantPOSWidget[restaurant_compact_mode="true"] QLabel#restaurantPOSTitle {{' in qss
    assert 'QFrame#restaurantOrderSummaryCard[restaurant_compact_mode="true"] {{' in qss


def test_phase297_local_restaurant_gateway_has_absolute_feature_import_fallback():
    source = open("alrajhi_client/gateways/local/restaurant_gateway.py", "r", encoding="utf-8").read()
    assert "except ModuleNotFoundError" in source
    assert "alrajhi_client.features.restaurant.restaurant_order_state" in source
    assert "alrajhi_client.features.restaurant.restaurant_payment_split_policy" in source
