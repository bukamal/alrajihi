#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate the shipped Arabic/German/English/French translation bundle."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "alrajhi_client"))

CRITICAL_KEYS = [
    "app_title", "dashboard", "items", "categories", "customers", "suppliers",
    "sales_invoice", "purchase_invoice", "sales_returns", "purchase_returns",
    "receipt_voucher", "payment_voucher", "manufacturing", "settings", "reports",
    "save", "print_report", "restaurant.dashboard", "restaurant.kitchen_display",
    "workspace.quick_open", "workspace.recent_tabs", "workspace.favorites",
]


def main() -> int:
    from i18n import translator
    translator.load_translations()
    data = getattr(translator, "_translations", {})
    errors: list[str] = []
    for lang in translator.SUPPORTED_LANGUAGES:
        if lang not in data:
            errors.append(f"Missing language dictionary: {lang}")
            continue
        for key in CRITICAL_KEYS:
            if key not in data[lang] or not str(data[lang][key]).strip():
                errors.append(f"Missing critical translation {lang}.{key}")
    for lang in ("ar", "de", "en", "fr"):
        direction = translator.language_direction(lang)
        if lang == "ar" and direction != "rtl":
            errors.append("Arabic must be RTL")
        if lang in {"de", "en", "fr"} and direction != "ltr":
            errors.append(f"{lang} must be LTR")
    if errors:
        print("Release translations guard failed:")
        for e in errors:
            print(f" - {e}")
        return 1
    print("Release translations guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
