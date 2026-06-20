# -*- coding: utf-8 -*-
"""Phase 247: guard real print templates against packaged SyntaxError regressions."""
from pathlib import Path
import py_compile
import sys

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_print_templates_py_compiles_without_fstring_syntax_error(tmp_path):
    py_compile.compile(
        str(ROOT / "alrajhi_client" / "printing" / "print_templates.py"),
        doraise=True,
    )


def test_invoice_html_real_template_executes_without_bootstrap_error(monkeypatch):
    sys.path.insert(0, str(ROOT / "alrajhi_client"))
    try:
        from printing import print_templates
        html = print_templates.invoice_html({
            "type": "purchase",
            "reference": "P-247",
            "date": "2026-06-20",
            "supplier_name": "Phase 247 Supplier",
            "lines": [],
            "total": "0.00",
        })
    finally:
        try:
            sys.path.remove(str(ROOT / "alrajhi_client"))
        except ValueError:
            pass

    assert "PRINT-TEMPLATE-BOOTSTRAP-UNAVAILABLE" not in html
    assert "PRINT-TEMPLATE-UNAVAILABLE" not in html
    assert "brand-table" in html
    assert "P-247" in html


def test_invoice_qr_label_avoids_nested_double_quoted_fstring_regression():
    text = read("alrajhi_client/printing/print_templates.py")
    assert 'qr_label = _s(_tr("print_document_qr"))' in text
    assert "{qr_label}" in text
    assert 'qr_html = f"<table class=\'qr-table\'' in text
    assert '{_s(_tr("print_document_qr"))}' not in text
