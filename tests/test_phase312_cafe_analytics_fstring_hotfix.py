from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYTICS_WIDGET = ROOT / "alrajhi_client" / "views" / "restaurant" / "restaurant_analytics_widget.py"


def test_restaurant_analytics_widget_is_parseable() -> None:
    source = ANALYTICS_WIDGET.read_text(encoding="utf-8")
    ast.parse(source)


def test_cafe_status_line_avoids_nested_translation_fstring_calls() -> None:
    source = ANALYTICS_WIDGET.read_text(encoding="utf-8")
    assert 'f"{_("restaurant.cafe_top_modifier")}' not in source
    assert 'top_modifier_label = _("restaurant.cafe_top_modifier")' in source
    assert 'low_stock_label = _("restaurant.cafe_low_stock_alerts")' in source
    assert 'top_modifier_name = (top_modifiers[0] if top_modifiers else {}).get("name") or "—"' in source
