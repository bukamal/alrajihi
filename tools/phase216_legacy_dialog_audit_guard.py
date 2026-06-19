#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 216 guard: legacy dialog audit and dashboard quick-action routing.

This guard intentionally allows small modal utilities (login, camera scanner,
column chooser, password dialogs, etc.). It blocks the dashboard from reopening
large legacy document/CRUD dialogs that now have workspace document tabs.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "alrajhi_client" / "views" / "widgets" / "dashboard_widget.py"
TRANSLATOR = ROOT / "alrajhi_client" / "i18n" / "translator.py"

FORBIDDEN_DASHBOARD_DIALOG_IMPORTS = {
    "views.dialogs.invoice_dialog",
    "views.dialogs.add_entity_dialog",
    "views.dialogs.item_dialog",
    "views.dialogs.bom_dialog",
    "views.dialogs.production_order_dialog",
    "views.dialogs.production_details_dialog",
}

REQUIRED_DASHBOARD_METHOD_CALLS = {
    "_open_invoice": "open_quick_invoice",
    "_open_add_customer": "open_party_document",
    "_open_add_supplier": "open_party_document",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _function_source(tree: ast.AST, name: str, source: str) -> str:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Missing dashboard method: {name}")


def _dashboard_imports_are_clean() -> None:
    source = _read(DASHBOARD)
    tree = ast.parse(source, filename=str(DASHBOARD))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in FORBIDDEN_DASHBOARD_DIALOG_IMPORTS:
            violations.append(f"line {node.lineno}: from {node.module} import ...")
    if violations:
        raise AssertionError("Dashboard still imports legacy document dialogs:\n" + "\n".join(violations))

    for method, required_call in REQUIRED_DASHBOARD_METHOD_CALLS.items():
        segment = _function_source(tree, method, source)
        if required_call not in segment:
            raise AssertionError(f"{method} must route through MainWindow.{required_call}()")
    if "InvoiceDialog(" in source or "AddEntityDialog(" in source:
        raise AssertionError("Dashboard still instantiates InvoiceDialog/AddEntityDialog directly")


def _translation_key_exists() -> None:
    text = _read(TRANSLATOR)
    for lang_marker in ("ar.update", "de.update", "en.update"):
        idx = text.find(lang_marker)
        if idx < 0:
            raise AssertionError(f"Missing translation block: {lang_marker}")
    if text.count("cannot_open_document_tab") < 3:
        raise AssertionError("cannot_open_document_tab must be translated in ar/de/en")


def _legacy_dialog_inventory() -> dict[str, list[str]]:
    """Return a lightweight inventory for informational CI output."""
    dialog_dir = ROOT / "alrajhi_client" / "views" / "dialogs"
    dialogs = sorted(p.name for p in dialog_dir.glob("*.py") if p.name != "__init__.py")
    usages: list[str] = []
    for path in (ROOT / "alrajhi_client").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "views.dialogs" in text:
            usages.append(rel)
    return {"dialogs": dialogs, "dialog_import_users": sorted(set(usages))}


def main() -> int:
    _dashboard_imports_are_clean()
    _translation_key_exists()
    inventory = _legacy_dialog_inventory()
    print("Phase 216 legacy dialog audit passed")
    print(f"Legacy dialog files: {len(inventory['dialogs'])}")
    print(f"Files still importing views.dialogs: {len(inventory['dialog_import_users'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
