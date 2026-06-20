# -*- coding: utf-8 -*-
"""Phase 248: invoice browser print must respect display currency and Decimal-safe formatting.

The print template receives display-currency amounts from the transaction UI/API.
It must format those values exactly for presentation; it must not perform a second
currency conversion and must not leak binary float/Decimal residue into HTML.
"""
from __future__ import annotations

from pathlib import Path
import importlib.util
import py_compile

ROOT = Path(__file__).resolve().parents[1]


def _load_templates():
    path = ROOT / "alrajhi_client" / "printing" / "print_templates.py"
    spec = importlib.util.spec_from_file_location("phase248_print_templates", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_print_template_and_settings_service_compile_after_currency_hotfix():
    py_compile.compile(str(ROOT / "alrajhi_client" / "printing" / "print_templates.py"), doraise=True)
    py_compile.compile(str(ROOT / "alrajhi_client" / "core" / "services" / "settings_service.py"), doraise=True)


def test_invoice_print_formats_syp_money_without_float_residue(monkeypatch):
    templates = _load_templates()
    monkeypatch.setattr(templates, "_settings", lambda: {
        "display_currency": "SYP",
        "currency_decimals": "2",
        "number_format": "western",
        "show_logo": False,
        "show_qr": False,
        "reverse_print_table_columns": False,
        "invoice_template": "a4",
        "default_paper": "a4",
    })
    monkeypatch.setattr(templates, "_settings_service", lambda: None)

    html = templates.invoice_html({
        "type": "purchase",
        "reference": "PUR-2026-0003",
        "date": "2026-06-20",
        "supplier_name": "بدون طرف",
        "currency": "SYP",
        "lines": [
            {"barcode": "2903857541437", "item_name": "خشب", "unit": "لوح", "quantity": 10, "unit_price": 30000.000000000000, "line_total": 300000.000000000000},
            {"barcode": "2905193975051", "item_name": "دهان", "unit": "لتر", "quantity": 10, "unit_price": 14999.999999999999, "line_total": 149999.999999999999},
            {"barcode": "2900543001640", "item_name": "مسامير", "unit": "كيلو", "quantity": 10, "unit_price": "10000.000000000000", "line_total": "100000.000000000000"},
        ],
        "subtotal": "550000.000000000000",
        "discount": 0,
        "tax_amount": 0,
        "total": "549999.999999999999999999999",
        "paid": "550000.0",
        "remaining": "1E-22-",
    })

    assert "SYP ل.س" in html
    assert "30,000.00 ل.س" in html
    assert "300,000.00 ل.س" in html
    assert "15,000.00 ل.س" in html
    assert "150,000.00 ل.س" in html
    assert "10,000.00 ل.س" in html
    assert "100,000.00 ل.س" in html
    assert "550,000.00 ل.س" in html
    assert "1E-22" not in html
    assert "549999.999" not in html
    assert "14999.999" not in html
    assert "300000.000" not in html


def test_invoice_print_uses_document_currency_symbol_without_converting(monkeypatch):
    templates = _load_templates()
    monkeypatch.setattr(templates, "_settings", lambda: {
        "display_currency": "USD",
        "currency_decimals": "2",
        "number_format": "western",
        "show_logo": False,
        "show_qr": False,
        "reverse_print_table_columns": False,
        "invoice_template": "a4",
        "default_paper": "a4",
    })
    monkeypatch.setattr(templates, "_settings_service", lambda: None)

    html = templates.invoice_html({
        "type": "purchase",
        "reference": "PUR-SYP-DOC",
        "currency": "SYP",
        "lines": [{"item_name": "خشب", "quantity": 1, "unit_price": 30000, "line_total": 30000}],
        "total": 30000,
        "paid": 0,
        "remaining": 30000,
    })

    assert "30,000.00 ل.س" in html
    assert "30,000.00 $" not in html
    assert "2.14" not in html  # guards against accidental SYP->USD conversion-like output


def test_purchase_invoice_prefers_supplier_name_over_generic_entity_and_localizes_cash(monkeypatch):
    templates = _load_templates()
    monkeypatch.setattr(templates, "_settings", lambda: {
        "display_currency": "SYP",
        "currency_decimals": "2",
        "number_format": "western",
        "show_logo": False,
        "show_qr": False,
        "reverse_print_table_columns": False,
        "invoice_template": "a4",
        "default_paper": "a4",
    })
    monkeypatch.setattr(templates, "_settings_service", lambda: None)

    html = templates.invoice_html({
        "type": "purchase",
        "reference": "PUR-PARTY",
        "supplier_name": "بدون طرف",
        "entity_name": "نقدي",
        "payment_method": "cash",
        "currency": "SYP",
        "lines": [],
        "total": 0,
    })

    assert "بدون طرف" in html
    # The supplier field must not be polluted by payment method/entity fallback.
    assert "<span class='meta-value'>نقدي</span></td></tr>" not in html
    assert any(token in html for token in ("نقد", "Cash", "Bar", "payment_cash"))
