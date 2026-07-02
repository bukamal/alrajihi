# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_restaurant_simple_material_grid_is_3_to_4_columns():
    src = read("alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py")
    grid = read("alrajhi_client/ui/operational_item_card_grid.py")
    assert "restaurantCardGridPhase" in src
    assert "default_columns=3" in src
    assert "min_columns=3" in src
    assert "max_columns=4" in src
    assert "self.splitter.setStretchFactor(1, 4)" in src
    assert "self.splitter.setSizes([150, 520, 440])" in src
    assert 'self.mode in {"restaurant", "cafe"}' in grid
    assert "return max(self.min_columns, self.default_columns)" in grid


def test_restaurant_legacy_pos_menu_grid_uses_same_card_contract():
    src = read("alrajhi_client/views/restaurant/restaurant_pos_widget.py")
    assert "restaurantMenuOperationalItemCardGrid" in src
    assert "restaurantCardGridPhase" in src
    assert "default_columns=3" in src
    assert "min_columns=3" in src
    assert "max_columns=4" in src


def test_restaurant_receipt_print_checks_out_paid_before_printing():
    simple = read("alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py")
    legacy = read("alrajhi_client/views/restaurant/restaurant_pos_widget.py")
    bridge = read("alrajhi_client/features/restaurant/restaurant_printing_bridge.py")
    template = read("alrajhi_client/printing/print_templates.py")
    for src in (simple, legacy):
        assert "checkout_simple_pos_session" in src
        assert "restaurant_printing_bridge.receipt_print" in src
        assert "restaurant.receipt_printed_paid" in src
    assert 'payload["payment_status"] = "paid"' in bridge
    assert 'paid_receipt_enforced' in bridge
    assert "restaurant.receipt_payment_status" in template
    assert "restaurant.receipt_paid" in template


def test_restaurant_paid_receipt_i18n_covers_all_languages():
    tr = read("alrajhi_client/i18n/translator.py")
    for key in [
        "restaurant.receipt_payment_status",
        "restaurant.receipt_paid",
        "restaurant.receipt_unpaid",
        "restaurant.receipt_printed_paid",
    ]:
        assert tr.count(key) >= 4, key
