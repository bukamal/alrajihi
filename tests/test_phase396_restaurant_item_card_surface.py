# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_restaurant_items_use_same_single_column_card_surface_as_categories():
    src = read("alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py")
    assert "restaurant_same_card_surface" in src
    assert "button.setMinimumHeight(58)" in src
    assert "button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)" in src
    assert "self.items_grid.addWidget(button, index, 0)" in src
    assert "self.items_grid.setRowStretch(len(self.menu_items), 1)" in src


def test_restaurant_items_no_longer_use_responsive_multicolumn_tiles():
    src = read("alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py")
    assert "columns = 3 if self.width() >= 1200 else 2" not in src
    assert "index // columns, index % columns" not in src
    resize_block = src.split("def resizeEvent", 1)[1].split("def start_new_sale", 1)[0]
    assert "self._render_items()" not in resize_block


def test_quality_contract_documents_item_card_surface():
    contract = read("alrajhi_client/workspace/quality/restaurant_item_card_surface_contract.py")
    assert "RESTAURANT_ITEM_CARD_SURFACE_CONTRACT" in contract
    assert "single-column rectangular card" in contract
    assert "restaurant_same_card_surface" in contract
