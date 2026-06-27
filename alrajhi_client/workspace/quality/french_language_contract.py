# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 392 quality contract: French is a first-class UI/print/report language."""

from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def french_language_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    root = root or ROOT
    import sys
    sys.path.insert(0, str(root / "alrajhi_client"))
    from i18n import translator

    translator.load_translations()
    data = getattr(translator, "_translations", {})
    fr = data.get("fr", {})
    ar = data.get("ar", {})
    en = data.get("en", {})
    required_keys = [
        "app_title", "language_fr", "dashboard", "sales_invoice", "purchase_invoice",
        "sales_returns", "purchase_returns", "items", "manufacturing", "reports",
        "settings_print_language_label", "print_report", "report_opened_in_browser",
        "transaction_column_item", "transaction_column_unit", "transaction_column_price",
        "settings_surface_title", "barcode.profile.items.default.title",
    ]
    translator.set_language("fr")
    rows: List[Dict[str, object]] = []
    rows.append({
        "check": "supported_language_registry",
        "area": "i18n",
        "detail": "French is present in SUPPORTED_LANGUAGES and available_languages.",
        "passed": "fr" in translator.SUPPORTED_LANGUAGES and any(code == "fr" for code, _ in translator.available_languages()),
    })
    rows.append({
        "check": "french_direction",
        "area": "i18n",
        "detail": "French uses LTR layout direction.",
        "passed": translator.language_direction("fr") == "ltr",
    })
    rows.append({
        "check": "french_coverage_ar",
        "area": "i18n",
        "detail": "French dictionary covers every Arabic source key.",
        "passed": bool(fr) and not (set(ar) - set(fr)),
    })
    rows.append({
        "check": "french_coverage_en",
        "area": "i18n",
        "detail": "French dictionary covers every English migrated key.",
        "passed": bool(fr) and not (set(en) - set(fr)),
    })
    for key in required_keys:
        value = translator.translate(key)
        rows.append({
            "check": f"fr_key_{key}",
            "area": "i18n",
            "detail": f"Critical French translation exists for {key}.",
            "passed": bool(value and value != key),
        })
    settings_tabs = _read("alrajhi_client/features/settings/settings_document_tabs.py")
    rows.append({
        "check": "settings_document_language_choices",
        "area": "settings",
        "detail": "UI/report/print language choices expose fr.",
        "passed": settings_tabs.count("choice:ar|en|de|fr") >= 3,
    })
    loader = _read("alrajhi_client/printing/_template_loader.py")
    rows.append({
        "check": "emergency_print_template_fr",
        "area": "printing",
        "detail": "Emergency print template fallback has French labels.",
        "passed": "'fr':" in loader and "Facture d’origine" in loader and "Le modèle d’impression" in loader,
    })
    translator_source = _read("alrajhi_client/i18n/translator.py")
    rows.append({
        "check": "no_legacy_french_fallback",
        "area": "i18n",
        "detail": "French no longer falls back to Arabic.",
        "passed": "French is no longer supported" not in translator_source and '"fr": "ar"' not in translator_source,
    })
    return rows


def french_language_summary(root: Path | None = None) -> Dict[str, object]:
    rows = french_language_matrix(root)
    failed = [row for row in rows if not row.get("passed")]
    return {"checks": len(rows), "failed": len(failed), "passed": not failed, "failed_checks": failed}


__all__ = ["french_language_matrix", "french_language_summary"]
