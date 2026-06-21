from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase292_restaurant_pos_visual_contract():
    pos = (ROOT / "alrajhi_client" / "views" / "restaurant" / "restaurant_pos_widget.py").read_text(encoding="utf-8")
    qss = (ROOT / "alrajhi_client" / "theme" / "qss.py").read_text(encoding="utf-8")

    assert "restaurantOrderHeaderCard" in pos
    assert "restaurantOrderSummaryCard" in pos
    assert "restaurantOrderSummaryMetric" in pos
    assert "restaurantActionGroups" in pos
    assert "restaurantActionGroup" in pos
    assert "restaurant.action_group.kitchen" in pos
    assert "summary_values" in pos

    assert "restaurantOrderHeaderCard" in qss
    assert "restaurantOrderSummaryCard" in qss
    assert "restaurantOrderSummaryMetric" in qss
    assert "restaurantActionGroups" in qss
    assert "restaurantActionGroupTitle" in qss


def test_phase292_restaurant_user_facing_translations_present():
    from alrajhi_client.i18n import translator

    translator.set_language("ar")
    keys = [
        "restaurant.subtotal",
        "restaurant.discount",
        "restaurant.service_charge",
        "restaurant.tax",
        "restaurant.order_financial_summary",
        "restaurant.action_group.order",
        "restaurant.action_group.kitchen",
        "restaurant.action_group.payment",
    ]
    for key in keys:
        value = translator.translate(key)
        assert value != key
        assert not value.startswith("restaurant.")


def test_phase292_restaurant_kds_visual_contract():
    kds = (ROOT / "alrajhi_client" / "views" / "restaurant" / "kitchen_display_widget.py").read_text(encoding="utf-8")
    qss = (ROOT / "alrajhi_client" / "theme" / "qss.py").read_text(encoding="utf-8")

    assert "restaurantKDSBoardBody" in kds
    assert "def _status_icon" in kds
    assert "restaurantKDSBoardBody" in qss
    assert "restaurant.lines_count" in kds
