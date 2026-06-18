# -*- coding: utf-8 -*-
"""Phase 64 guard: enforce project-wide table standardization.

Read-only/model-backed tables must use SmartTableView. Editable line-entry or
matrix tables must use EditableSmartGrid. Direct QTableWidget construction and
legacy CustomTableView instantiation are blocked outside the standard wrapper
implementations and documented scanner helpers.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"

ALLOWED_QTABLEWIDGET_REFERENCES = {
    Path("alrajhi_client/ui/editable_smart_grid.py"),
    Path("alrajhi_client/features/dialog_documents/dialog_document_tab.py"),  # scans legacy embedded dialogs only
    Path("alrajhi_client/views/widgets/modern_ui.py"),  # applies styling/introspection only
}

REQUIRED_EDITABLE_GRID_FILES = {
    "alrajhi_client/views/widgets/settings_widget.py": [
        "settings.rates", "settings.profiles", "settings.audit", "settings.security_events"
    ],
    "alrajhi_client/views/widgets/offline_queue_widget.py": ["offline_queue.list"],
    "alrajhi_client/views/widgets/monitoring_widget.py": ["monitoring.overview"],
    "alrajhi_client/views/widgets/pos_widget.py": ["pos.lines"],
    "alrajhi_client/views/widgets/returns_widget.py": ["returns.lines"],
    "alrajhi_client/features/items/item_editor_tab.py": ["items.units"],
    "alrajhi_client/views/dialogs/item_dialog.py": ["item_dialog.units"],
}

REQUIRED_SMART_TABLE_FILES = {
    "alrajhi_client/views/dialogs/batch_print_dialog.py": ["batch_print.items"],
    "alrajhi_client/views/dialogs/production_order_dialog.py": ["production_order.materials"],
    "alrajhi_client/views/dialogs/production_details_dialog.py": [
        "production_details.consumption", "production_details.output"
    ],
}


def rel(path: Path) -> Path:
    return path.relative_to(ROOT)


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def main() -> int:
    errors: list[str] = []
    for path in CLIENT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            errors.append(f"{rel(path)}: syntax error: {exc}")
            continue
        relative = rel(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = call_name(node.func)
                if name == "QTableWidget" and relative not in ALLOWED_QTABLEWIDGET_REFERENCES:
                    errors.append(f"{relative}:{node.lineno}: direct QTableWidget construction; use EditableSmartGrid")
                if name == "CustomTableView" and relative != Path("alrajhi_client/ui/smart_table_view.py"):
                    errors.append(f"{relative}:{node.lineno}: direct CustomTableView construction; use SmartTableView")

    for file_name, identities in REQUIRED_EDITABLE_GRID_FILES.items():
        path = ROOT / file_name
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        if "EditableSmartGrid" not in text:
            errors.append(f"{file_name}: missing EditableSmartGrid")
        for identity in identities:
            if identity not in text:
                errors.append(f"{file_name}: missing editable grid identity {identity}")

    for file_name, identities in REQUIRED_SMART_TABLE_FILES.items():
        path = ROOT / file_name
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        if "SmartTableView" not in text:
            errors.append(f"{file_name}: missing SmartTableView")
        for identity in identities:
            if identity not in text:
                errors.append(f"{file_name}: missing smart table identity {identity}")

    if errors:
        print("Full table standardization guard failed:")
        for err in errors:
            print(f" - {err}")
        return 1
    print("Full table standardization guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
