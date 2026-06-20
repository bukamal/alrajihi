# -*- coding: utf-8 -*-
"""Phase 242: all legacy print paths must converge to browser HTML and print-language settings."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_printing_service_has_no_qt_print_dialog_or_pdf_renderer():
    text = read("alrajhi_client/printing/printing_service.py")
    assert "QPrintDialog" not in text
    assert "QPrintPreviewDialog" not in text
    assert "PdfFormat" not in text
    assert "def render_html" in text
    assert "return self.open_html_in_browser" in text
    assert "Legacy modes (preview/direct/print/pdf/export)" in text


def test_legacy_print_manager_is_browser_html_only():
    text = read("alrajhi_client/printing/print_manager.py")
    assert "QtPrintSupport" not in text
    assert "PrinterManager" not in text
    assert "printer_id'] = 'browser'" in text
    assert "printing_service.render_html" in text


def test_thermal_and_pdf_label_paths_open_browser_html():
    text = read("alrajhi_client/printing/thermal_printer.py")
    assert "QtPrintSupport" not in text
    assert "PdfFormat" not in text
    assert "printing_service.open_html_in_browser" in text
    assert "labels_document_html" in text


def test_print_templates_translate_with_print_language_not_ui_global():
    text = read("alrajhi_client/printing/print_templates.py")
    assert "settings_service.print_language()" in text
    assert "avoid relying on the translator's global" in text
    assert "_TITLE_MAP" in text
    assert "return _tr(_TITLE_MAP[key])" in text


def test_fallback_template_has_language_aware_labels():
    text = read("alrajhi_client/printing/_template_loader.py")
    assert "def _fallback_text" in text
    assert "'de'" in text and "'en'" in text and "'ar'" in text
    assert '_fallback_text("sales_invoice")' in text
