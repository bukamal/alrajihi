import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_restaurant_page_is_registered_in_main_window():
    source = _read("alrajhi_client/views/main_window.py")
    tree = ast.parse(source)
    constants = {node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    assert "restaurant" in constants
    assert "restaurant.dashboard" in constants
    assert "nav_restaurant" in constants
    assert "F8" in constants
    assert "RestaurantDashboard" in source


def test_restaurant_touch_widgets_are_thin_ui_wrappers():
    for relative in (
        "alrajhi_client/views/restaurant/restaurant_dashboard.py",
        "alrajhi_client/views/restaurant/restaurant_pos_widget.py",
        "alrajhi_client/views/restaurant/table_map_widget.py",
    ):
        tree = ast.parse(_read(relative), filename=relative)
        text_literals = "\n".join(
            node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        ).upper()
        assert "SELECT " not in text_literals
        assert "INSERT " not in text_literals
        assert "UPDATE " not in text_literals
        assert "DELETE " not in text_literals


def test_phase21_translation_keys_exist_for_all_languages():
    from alrajhi_client.i18n import translator

    keys = [
        "nav_restaurant",
        "restaurant.add_item",
        "restaurant.close_table",
        "restaurant.current_total",
        "restaurant.status.occupied",
    ]
    for lang in ("ar", "de", "en"):
        translator.set_language(lang)
        for key in keys:
            assert translator.translate(key) != key
