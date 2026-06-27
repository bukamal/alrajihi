# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_basit_palette_and_metrics_are_central_theme_tokens():
    brand = read("alrajhi_client/theme/brand.py")
    for token in ["BASIT_BLUE", "BASIT_YELLOW", "BASIT_RED", "BASIT_GREY"]:
        assert token in brand
    for key in ["basit_pos_card_height", "basit_category_card_height", "basit_invoice_row_height", "basit_total_height", "basit_toolbar_height"]:
        assert key in brand


def test_global_qss_renders_basit_skin_without_fstring_errors():
    from theme.brand import get_tokens
    from theme.qss import build_global_qss

    qss = build_global_qss(get_tokens("light"))
    assert "Phase401: Basit inspired operational skin" in qss
    assert "#restaurantSimpleItemButton" in qss
    assert "#restaurantSimpleTotal" in qss
    assert "dashboard_shortcut" in qss
    assert "#0076D7" in qss
    assert "#D93600" in qss


def test_restaurant_simple_pos_is_bound_to_basit_visual_properties():
    src = read("alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py")
    assert 'self.setProperty("basitInspired", True)' in src
    assert 'self.invoice_table.setProperty("basitTable", True)' in src
    assert 'self.total_label.setProperty("basitTotal", True)' in src
    assert 'button.setProperty("basitCard", True)' in src
    assert 'self.splitter.setSizes([270, 360, 720])' in src


def test_quality_contract_documents_basit_visual_system():
    contract = read("alrajhi_client/workspace/quality/basit_visual_system_contract.py")
    assert "BASIT_VISUAL_SYSTEM_CONTRACT" in contract
    assert "restaurant_simple_pos" in contract
    assert "dashboard_shortcuts" in contract
