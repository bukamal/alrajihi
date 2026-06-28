# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _load_templates():
    path = ROOT / "alrajhi_client" / "printing" / "print_templates.py"
    spec = importlib.util.spec_from_file_location("phase408_print_templates", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_basit_print_token_bridge_is_present_and_theme_backed():
    text = read("alrajhi_client/printing/print_templates.py")
    assert "def _basit_print_tokens" in text
    assert "from theme.brand import LIGHT_TOKENS, DARK_TOKENS" in text
    assert "accent = basit['blue']" in text
    assert "Phase408: Basit-inspired print/export surface" in text


def test_invoice_html_uses_basit_print_colors_for_header_grid_and_total():
    templates = _load_templates()
    html = templates.invoice_html({
        "type": "sale",
        "reference": "S-408",
        "date": "2026-06-28",
        "customer_name": "زبون اختبار",
        "lines": [{"item_name": "مادة", "quantity": 2, "unit_price": 10, "line_total": 20}],
        "subtotal": 20,
        "total": 20,
        "paid": 20,
        "remaining": 0,
    })
    assert "#0076D7" in html or "#1268B3" in html
    assert "#F2D21B" in html
    assert "#D93600" in html or "#E64A19" in html
    assert "border-top: 6px solid" in html
    assert ".totals-table tr.final td" in html
    assert "background: #D93600" in html or "background: #E64A19" in html
    assert "brand-table" in html
    assert "data-table" in html


def test_report_restaurant_and_thermal_outputs_keep_basit_surface_markers():
    templates = _load_templates()
    report = templates.report_html("تقرير", [["A", "10"]], ["اسم", "قيمة"], summary={"إجمالي": "10"})
    receipt = templates.restaurant_receipt_html({
        "session": {"id": "R-408", "table_name": "1", "waiter": "Ali", "guests": 2},
        "items": [{"name": "قهوة", "qty": 1, "unit_price": 2, "total": 2}],
        "subtotal": 2,
        "total": 2,
        "paid": 2,
        "remaining": 0,
        "display_currency": "USD",
    }, paper="thermal")
    for html in (report, receipt):
        assert "border-top: 6px solid" in html or "border-bottom: 1px dashed" in html
        assert "#F2D21B" in html
        assert "#0076D7" in html or "#1268B3" in html
    assert "thermal80" in receipt or "thermal58" in receipt
    assert "box-shadow: none" in receipt


def test_contract_and_release_gate_include_phase408():
    contract = read("alrajhi_client/workspace/quality/basit_printing_surface_contract.py")
    release_gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert "BASIT_PRINTING_SURFACE_CONTRACT" in contract
    assert "invoice_html" in contract
    assert "restaurant_receipt_html" in contract
    assert "basit_printing_surface" in release_gate
    assert "BASIT_PRINTING_SURFACE" in release_gate
    assert "phase=408" in release_gate
