from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase296_dashboard_has_responsive_breakpoints_and_mode_sizes():
    dashboard = _read("alrajhi_client/views/restaurant/restaurant_dashboard.py")

    assert "RESTAURANT_RESPONSIVE_BREAKPOINTS" in dashboard
    assert '"compact": 1280' in dashboard
    assert '"wide": 1600' in dashboard
    assert "RESTAURANT_ORDER_SPLITTER_SIZES" in dashboard
    assert "RESTAURANT_KITCHEN_SPLITTER_SIZES" in dashboard
    assert "def _resolve_responsive_layout_mode" in dashboard
    assert "def _apply_responsive_layout" in dashboard
    assert "resizeEvent" in dashboard


def test_phase296_kitchen_mode_collapses_order_except_on_wide_workspace():
    dashboard = _read("alrajhi_client/views/restaurant/restaurant_dashboard.py")

    assert 'self._current_mode = "kitchen"' in dashboard
    assert 'self.pos.setVisible(self._current_mode == "order" or wide)' in dashboard
    assert '"compact": [360, 0, 780]' in dashboard
    assert '"standard": [360, 0, 860]' in dashboard
    assert '"wide": [420, 700, 560]' in dashboard


def test_phase296_table_operations_have_compact_menu():
    dashboard = _read("alrajhi_client/views/restaurant/restaurant_dashboard.py")
    qss = _read("alrajhi_client/theme/qss.py")

    assert "QToolButton" in dashboard
    assert "restaurantTableOperationsMenuButton" in dashboard
    assert "_apply_table_operations_compact_mode" in dashboard
    assert "QAction(button.text(), self)" in dashboard
    assert "restaurantTableOperationsMenuButton" in qss


def test_phase296_pos_has_compact_financial_summary_mode():
    pos = _read("alrajhi_client/views/restaurant/restaurant_pos_widget.py")
    qss = _read("alrajhi_client/theme/qss.py")

    assert "def set_restaurant_compact_mode" in pos
    assert "summary_metric_widgets" in pos
    assert 'decisive = {"total", "paid", "remaining"}' in pos
    assert "self.total_label.setVisible(not enabled)" in pos
    assert "restaurant_compact_mode" in pos
    assert 'restaurant_compact_mode="true"' in qss
