# -*- coding: utf-8 -*-
"""Phase 237 guard: visible print buttons must produce browser HTML from real templates."""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    service = read("alrajhi_client/printing/printing_service.py")
    loader = read("alrajhi_client/printing/_template_loader.py")
    templates = read("alrajhi_client/printing/print_templates.py")
    settings = read("alrajhi_client/core/services/settings_service.py")

    assert_true("'browser'" in service and "return 'browser'" in service, "print_button_mode must resolve visible print buttons to browser")
    assert_true("barcode_labels_print_settings" in service and "_print_button_render(html" in service, "barcode labels must use the same browser HTML print contract")
    assert_true("self.barcode_labels_print(items, parent, options, self.barcode_default_printer_name())" not in service, "barcode settings button must not bypass browser HTML")
    assert_true("QPrintDialog" in service, "low-level Qt print dialog may only remain inside printing_service for internal compatibility")

    assert_true("_MEIPASS" in loader, "template loader must inspect PyInstaller frozen root")
    assert_true("Successful imports are cached" in loader and "Failed imports are not cached" in loader, "template loader must not cache failed fallback lookups")
    assert_true("قالب طباعة احتياطي" not in loader, "browser output must not show emergency fallback warning text")
    assert_true("Report Html" not in loader, "fallback renderer must not expose technical template names")

    assert_true("from core.services.settings_service import settings_service" not in "\n".join(templates.splitlines()[:18]), "print_templates must lazy-load settings_service, not import it at module top")
    assert_true("def _settings_service" in templates, "print_templates must provide lazy settings service helper")
    assert_true("from config import get_company_info" not in templates, "print_templates must not depend on unused config import at module import time")

    assert_true("'print_button_mode': self.get('printing/print_button_mode', 'browser')" in settings, "printing settings default must be browser HTML")
    assert_true("barcode_default_printer: str = ''" in settings, "barcode printer default must not be pdf:default")
    assert_true("'barcode_default_printer': barcode_default_printer or ''" in settings, "saving print settings must not restore pdf:default")

    sys.path.insert(0, str(CLIENT))
    loader_mod = importlib.import_module("printing._template_loader")
    mod = loader_mod.load_print_templates()
    assert_true(mod is not None, "real print_templates module must load in source/runtime guard")
    report_html = loader_mod.require_template("report_html")
    html = report_html("InvoicesWidget.sales", [["A", "B"]], ["H1", "H2"], subtitle="عدد السجلات: 1")
    assert_true("قالب طباعة احتياطي" not in html, "report output must not use fallback warning")
    assert_true("Report Html" not in html, "report output must not use fallback template title")
    assert_true("<table" in html and "A" in html and "H1" in html, "report output must include real table content")

    samples = {
        "invoice_html": ({"type": "sale", "reference": "S-1", "lines": [{"item_name": "مادة", "quantity": "1", "unit_price": "10", "total": "10"}], "total": "10"}, "default"),
        "return_html": ({"type": "sale", "reference": "R-1", "lines": [{"item_name": "مادة", "quantity": "1", "unit_price": "10", "total": "10"}], "total": "10"}, "default"),
        "manufacturing_bom_html": ({"bom": {"bom_code": "BOM-1"}, "components": [{"item_name": "مادة", "qty": "1"}]}, "default"),
    }
    for name, args in samples.items():
        out = loader_mod.require_template(name)(*args)
        assert_true("قالب طباعة احتياطي" not in out, f"{name} must not use fallback warning")
        assert_true("<!DOCTYPE html>" in out and "<table" in out, f"{name} must render full browser HTML")

    print("Phase 237 browser HTML print guard passed")


if __name__ == "__main__":
    main()
