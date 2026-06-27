# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "alrajhi_client"))


def test_phase392_french_is_available_in_language_registry():
    from i18n import translator
    translator.load_translations()
    assert translator.normalize_language("fr") == "fr"
    assert translator.normalize_language("Français") == "fr"
    assert ("fr", "Français") in translator.available_languages()
    assert translator.language_direction("fr") == "ltr"


def test_phase392_french_dictionary_covers_ui_print_and_report_keys():
    from i18n import translator
    translator.load_translations()
    fr = translator._translations["fr"]
    assert set(translator._translations["ar"]) <= set(fr)
    assert set(translator._translations["en"]) <= set(fr)
    translator.set_language("fr")
    for key in [
        "app_title", "dashboard", "sales_invoice", "purchase_invoice",
        "sales_returns", "purchase_returns", "items", "manufacturing",
        "reports", "print_report", "settings_print_language_label",
        "transaction_column_item", "transaction_column_unit", "transaction_column_price",
        "barcode.profile.items.default.title", "settings_surface_title",
    ]:
        value = translator.translate(key)
        assert value and value != key


def test_phase392_language_choices_include_french_for_ui_print_and_reports():
    text = (ROOT / "alrajhi_client/features/settings/settings_document_tabs.py").read_text(encoding="utf-8")
    assert text.count("choice:ar|en|de|fr") >= 3


def test_phase392_print_fallback_has_french_labels():
    text = (ROOT / "alrajhi_client/printing/_template_loader.py").read_text(encoding="utf-8")
    assert "'fr':" in text
    assert "Facture d’origine" in text
    assert "Le modèle d’impression" in text


def test_phase392_guard_contract_ready_and_release_gate_registered():
    from workspace.quality.french_language_contract import french_language_summary
    summary = french_language_summary(ROOT)
    assert summary["passed"] is True
    gate = (ROOT / "alrajhi_client/workspace/quality/release_gate_contract.py").read_text(encoding="utf-8")
    assert "french_language" in gate
    assert "tools/phase392_french_language_guard.py" in gate
    assert '(392, "french_language")' in gate
