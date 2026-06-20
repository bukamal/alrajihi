# -*- coding: utf-8 -*-
"""Phase 245: missing real print templates must not silently print weak documents."""
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _load_loader():
    path = ROOT / "alrajhi_client" / "printing" / "_template_loader.py"
    spec = importlib.util.spec_from_file_location("phase245_template_loader", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_fallback_is_disabled_by_default_and_returns_visible_error(monkeypatch):
    loader = _load_loader()
    monkeypatch.setattr(loader, "load_print_templates", lambda: None)
    monkeypatch.setattr(loader, "_printing_setting", lambda key, default=None: False if key == "allow_emergency_fallback" else True)
    html = loader.require_template("invoice_html")({"type": "purchase", "reference": "X-245"})

    assert "PRINT-TEMPLATE-UNAVAILABLE" in html
    assert "print-template-error" in html
    assert "X-245" not in html  # no weak business document is produced silently
    assert "fallback-print" not in html


def test_emergency_fallback_is_explicitly_opt_in(monkeypatch):
    loader = _load_loader()
    monkeypatch.setattr(loader, "load_print_templates", lambda: None)
    monkeypatch.setattr(loader, "_printing_setting", lambda key, default=None: True if key in {"allow_emergency_fallback", "show_template_diagnostics"} else default)
    html = loader.require_template("invoice_html")({"type": "purchase", "reference": "X-245", "lines": []})

    assert "fallback-print-template" in html
    assert "Emergency print template used" in html
    assert "X-245" in html


def test_printing_settings_contract_exposes_fallback_policy_through_settings_service():
    text = read("alrajhi_client/core/services/settings_service.py")
    assert "printing/allow_emergency_fallback" in text
    assert "printing/show_template_diagnostics" in text
    assert "allow_emergency_fallback: bool = False" in text


def test_settings_ui_and_lightweight_document_tab_expose_policy():
    main_ui = read("alrajhi_client/views/widgets/settings_widget.py")
    doc_tab = read("alrajhi_client/features/settings/settings_document_tabs.py")
    assert "self.print_allow_emergency_fallback" in main_ui
    assert "self.print_show_template_diagnostics" in main_ui
    assert "printing/allow_emergency_fallback" in doc_tab
    assert "printing/show_template_diagnostics" in doc_tab


def test_policy_translations_exist_for_three_languages():
    text = read("alrajhi_client/i18n/translator.py")
    assert "settings_print_allow_emergency_fallback" in text
    assert "السماح بقالب طوارئ" in text
    assert "Einfache Notfallvorlage" in text
    assert "Allow a simplified emergency template" in text
