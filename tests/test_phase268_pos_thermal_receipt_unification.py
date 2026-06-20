# -*- coding: utf-8 -*-
"""Phase 268: POS thermal receipt uses the unified print contract.

The POS checkout path stores amounts in the application storage/base currency,
while the cashier and receipt must show the configured display currency.  The
POS receipt therefore has its own template entry point instead of reusing the
A4 invoice print path blindly.
"""
from __future__ import annotations

from pathlib import Path
import importlib.util
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase268_files_compile():
    for rel in [
        "alrajhi_client/printing/print_templates.py",
        "alrajhi_client/printing/printing_service.py",
        "alrajhi_client/views/widgets/pos_widget.py",
        "alrajhi_client/core/services/settings_service.py",
        "alrajhi_client/features/settings/settings_document_tabs.py",
    ]:
        py_compile.compile(str(ROOT / rel), doraise=True)


def test_pos_widget_uses_dedicated_pos_receipt_print_path():
    text = read("alrajhi_client/views/widgets/pos_widget.py")
    assert "printing_service.pos_receipt_print" in text
    assert "printing_service.invoice_print(inv, self, paper='thermal80')" not in text
    assert "receipt_paper" in text


def test_printing_service_exposes_pos_receipt_template_entry_points():
    text = read("alrajhi_client/printing/printing_service.py")
    assert 'pos_receipt_html = require_template("pos_receipt_html")' in text
    assert "def pos_receipt_html" in text
    assert "def pos_receipt_print" in text
    assert "document_type='pos_receipt'" in text


def test_pos_receipt_template_converts_storage_amounts_and_keeps_logo_header():
    sys.path.insert(0, str(CLIENT))
    try:
        path = CLIENT / "printing" / "print_templates.py"
        spec = importlib.util.spec_from_file_location("phase268_print_templates", path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        html = module.pos_receipt_html({
            "type": "sale",
            "reference": "SAL-POS-1",
            "date": "2026-06-20",
            "notes": "POS Fast Sale - cash",
            "total": "2.5",
            "paid": "2.5",
            "remaining": "0",
            "original_currency": "SYP",
            "exchange_rate_to_usd": "14000",
            "payment_method": "cash",
            "lines": [{"item_name": "خشب", "quantity": "5", "unit_price": "0.5", "total": "2.5"}],
        }, paper="thermal80")
    finally:
        try:
            sys.path.remove(str(CLIENT))
        except ValueError:
            pass
    assert "thermal80" in html
    assert "brand-logo" in html
    assert "35,000.00 ل.س" in html
    assert "7,000.00 ل.س" in html
    assert "print_barcode" not in html


def test_pos_settings_contract_contains_receipt_logo_and_qr_flags():
    settings = read("alrajhi_client/core/services/settings_service.py")
    tabs = read("alrajhi_client/features/settings/settings_document_tabs.py")
    assert "pos_receipt_show_logo" in settings
    assert "pos_receipt_show_qr" in settings
    assert "pos/receipt_show_logo" in tabs
    assert "pos/receipt_show_qr" in tabs
