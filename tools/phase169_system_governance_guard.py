# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 169 governance checks for the transaction document engine."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TX = ROOT / "alrajhi_client" / "features" / "transactions"

PROHIBITED_IMPORTS = (
    "database",
    "database.",
    "requests",
    "connection_rest",
)
ALLOWED_LITERAL_WIDGET_TEXT = {"0.00", "", "#"}


def iter_py_files():
    for path in TX.rglob("*.py"):
        if "__pycache__" not in path.parts:
            yield path


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def check_no_direct_qsettings(errors: list[str]) -> None:
    for path in iter_py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "PyQt5.QtCore":
                for alias in node.names:
                    if alias.name == "QSettings":
                        errors.append(f"{path}: direct QSettings import is forbidden in transactions")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.endswith("QSettings"):
                        errors.append(f"{path}: direct QSettings import is forbidden in transactions")


def check_no_low_level_access(errors: list[str]) -> None:
    for path in iter_py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            module = None
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    if any(name == bad or name.startswith(bad) for bad in PROHIBITED_IMPORTS):
                        errors.append(f"{path}: low-level import {name!r} is forbidden in transactions")
                continue
            if module and any(module == bad or module.startswith(bad) for bad in PROHIBITED_IMPORTS):
                errors.append(f"{path}: low-level import {module!r} is forbidden in transactions")


def _is_localized_expr(node: ast.AST) -> bool:
    if isinstance(node, ast.Call):
        return _call_name(node.func) in {"tr", "translate", "html_bold"}
    if isinstance(node, ast.JoinedStr):
        return True
    if isinstance(node, ast.Name):
        return True
    return False


def check_widget_text_localized(errors: list[str]) -> None:
    constructors = {"QLabel", "QPushButton"}
    text_methods = {"setText", "setPlaceholderText", "setToolTip"}
    for path in iter_py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node.func)
            if name in constructors and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str) and first.value not in ALLOWED_LITERAL_WIDGET_TEXT:
                    errors.append(f"{path}:{node.lineno} literal widget text must use tr(): {first.value!r}")
                elif not isinstance(first, ast.Constant) and not _is_localized_expr(first):
                    errors.append(f"{path}:{node.lineno} widget text must use tr()/translate/html_bold or a variable")
            if name in text_methods and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str) and first.value not in ALLOWED_LITERAL_WIDGET_TEXT:
                    errors.append(f"{path}:{node.lineno} literal UI text must use tr(): {first.value!r}")


def check_no_unsafe_barcode_fallback(errors: list[str]) -> None:
    doc = TX / "transaction_document_tab.py"
    text = doc.read_text(encoding="utf-8")
    banned = [
        "product_service.item_by_barcode(text) or",
        "catalog_service.items(search=text, limit=1)",
    ]
    for marker in banned:
        if marker in text:
            errors.append(f"{doc}: unsafe barcode/manual-search fallback still present: {marker}")
    if "barcode_input_service.lookup_entry" not in text:
        errors.append(f"{doc}: transaction input must use barcode_input_service.lookup_entry")


def main() -> None:
    errors: list[str] = []
    check_no_direct_qsettings(errors)
    check_no_low_level_access(errors)
    check_widget_text_localized(errors)
    check_no_unsafe_barcode_fallback(errors)
    if errors:
        raise SystemExit("\n".join(errors))
    print("phase169_system_governance_guard passed")


if __name__ == "__main__":
    main()
