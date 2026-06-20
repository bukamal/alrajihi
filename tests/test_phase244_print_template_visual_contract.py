# -*- coding: utf-8 -*-
"""Phase 244 guards: visual browser HTML print contract.

The tests are deliberately pure-Python so they protect the browser HTML template
without requiring PyQt, a server, or a printer.  Settings are still reached via
SettingsService/SettingsGateway when available, preserving the network/profile
contract from the application code path.
"""
from __future__ import annotations

from pathlib import Path
import importlib.util


def _load_templates():
    path = Path(__file__).resolve().parents[1] / "alrajhi_client" / "printing" / "print_templates.py"
    spec = importlib.util.spec_from_file_location("phase244_print_templates", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_invoice_browser_html_has_single_title_slot_and_professional_sheet():
    templates = _load_templates()
    html = templates.invoice_html({
        "type": "purchase",
        "reference": "PUR-TEST-244",
        "date": "2026-06-20",
        "supplier_name": "مورد اختبار",
        "lines": [{"item_name": "خشب", "unit": "لوح", "quantity": 1, "unit_price": 10, "line_total": 10}],
        "total": 10,
    })

    assert "brand-table" in html
    assert "document-badge" in html
    assert "class='document-title'" not in html
    assert "box-shadow: 0 10px 30px" in html
    assert "@media print" in html
    assert "sheet" in html


def test_company_header_does_not_render_empty_logo_placeholder():
    templates = _load_templates()
    html = templates.base_document("Test", templates._company_header({"show_logo": False}, "Test"), "a4", {"show_logo": False})

    assert "brand-logo placeholder" not in html
    assert "document-badge" in html


def test_thermal_template_keeps_browser_html_and_removes_desktop_shadow():
    templates = _load_templates()
    html = templates.invoice_html({"type": "sale", "reference": "S-1", "lines": []}, paper="thermal")

    assert "thermal80" in html or "thermal58" in html
    assert "box-shadow: none" in html
    assert "@page" in html
    assert "browser" not in html.lower() or "<!DOCTYPE html>" in html
