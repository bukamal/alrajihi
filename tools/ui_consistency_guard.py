#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 54 UI consistency guard.

Keeps the post-workspace UI direction explicit:
- Business CRUD/document flows must be opened through Workspace/DocumentTabs.
- Large legacy dialogs may remain only if they are listed as migration debt.
- UnifiedActionBar/UnifiedPrinting/SmartTableView must stay wired.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"

# Explicit migration debt. These files are allowed to exist while Phase 55+
# decomposes them; adding new large widgets/dialogs should fail this guard.
ALLOWED_HEAVY_UI = {
    "alrajhi_client/views/main_window.py",  # shell orchestration; pending Phase 55 split
    "alrajhi_client/views/dialogs/invoice_dialog.py",  # being decomposed through invoice document components
    "alrajhi_client/views/widgets/returns_widget.py",  # bridged by returns document tabs; pending full split
    "alrajhi_client/views/widgets/settings_widget.py",  # settings sections now have document tabs; legacy widget pending removal
}

ALLOWED_DIALOG_FILES = {
    # Framework / utility dialogs
    "alrajhi_client/main.py",
    "alrajhi_client/views/frameless_dialog.py",
    "alrajhi_client/shell/quick_open_dialog.py",
    "alrajhi_client/ui/smart_table_view.py",  # utility column chooser; not a business CRUD dialog
    "alrajhi_client/printing/print_manager.py",
    "alrajhi_client/views/dialogs/batch_print_dialog.py",
    "alrajhi_client/features/dialog_documents/dialog_document_tab.py",
    "alrajhi_client/features/returns/return_editor_tabs.py",
    # Legacy business dialogs/widgets that must not be used as new patterns.
    "alrajhi_client/views/dialogs/invoice_dialog.py",
    "alrajhi_client/views/dialogs/item_dialog.py",
    "alrajhi_client/views/dialogs/bom_dialog.py",
    "alrajhi_client/views/dialogs/production_details_dialog.py",
    "alrajhi_client/views/restaurant/restaurant_pos_widget.py",
    "alrajhi_client/views/widgets/audit_log_widget.py",
    "alrajhi_client/views/widgets/branches_widget.py",
    "alrajhi_client/views/widgets/cashboxes_widget.py",
    "alrajhi_client/views/widgets/categories_widget.py",
    "alrajhi_client/views/widgets/customers_widget.py",
    "alrajhi_client/views/widgets/returns_widget.py",
    "alrajhi_client/views/widgets/settings_widget.py",
    "alrajhi_client/views/widgets/users_widget.py",
    "alrajhi_client/views/widgets/vouchers_widget.py",
    "alrajhi_client/views/widgets/warehouses_widget.py",
}

REQUIRED_FILES = [
    "alrajhi_client/workspace/documents/base_document_tab.py",
    "alrajhi_client/shell/tab_workspace.py",
    "alrajhi_client/shell/unified_action_bar.py",
    "alrajhi_client/ui/smart_table_view.py",
    "alrajhi_client/features/dialog_documents/dialog_document_tab.py",
]

REQUIRED_MAIN_TOKENS = [
    "TabbedWorkspace",
    "UnifiedActionBar",
    "open_item_document",
    "open_category_document",
    "open_quick_invoice",
    "open_return_document",
    "open_party_document",
    "open_quick_voucher",
    "open_settings_section_document",
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def parse_all(errors: list[str]) -> None:
    for path in CLIENT.rglob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"syntax error: {rel(path)}:{exc.lineno}: {exc.msg}")


def guard_required_wiring(errors: list[str]) -> None:
    for file_name in REQUIRED_FILES:
        if not (ROOT / file_name).exists():
            errors.append(f"missing required workspace UI file: {file_name}")
    main_path = ROOT / "alrajhi_client/views/main_window.py"
    main_text = main_path.read_text(encoding="utf-8") if main_path.exists() else ""
    for token in REQUIRED_MAIN_TOKENS:
        if token not in main_text:
            errors.append(f"main_window missing workspace/document hook: {token}")

    action_bar = (ROOT / "alrajhi_client/shell/unified_action_bar.py").read_text(encoding="utf-8")
    if any(token in action_bar for token in ("QPrintDialog", "QPrinter", "QTextDocument", "DatabaseConnection", ".execute(", ".query(")):
        errors.append("UnifiedActionBar must stay UI-command only: no printing implementation or data access")

    smart_table = (ROOT / "alrajhi_client/ui/smart_table_view.py").read_text(encoding="utf-8")
    if "print_table" not in smart_table or "export" not in smart_table.lower():
        errors.append("SmartTableView must keep unified print/export surface")


def guard_large_files(errors: list[str]) -> None:
    ui_roots = (CLIENT / "views", CLIENT / "features", CLIENT / "shell", CLIENT / "ui")
    for base in ui_roots:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            rel_path = rel(path)
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if len(lines) > 900 and rel_path not in ALLOWED_HEAVY_UI:
                errors.append(f"large UI file must be decomposed or allowlisted: {rel_path} ({len(lines)} lines)")


def guard_dialog_policy(errors: list[str]) -> None:
    for path in CLIENT.rglob("*.py"):
        rel_path = rel(path)
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "QDialog" in text and rel_path not in ALLOWED_DIALOG_FILES and "theme/qss.py" not in rel_path:
            # We do not ban tiny confirmation/utility dialogs globally, but any new
            # business dialog must be explicitly listed so it cannot silently bypass Workspace.
            if "class " in text or "QDialog(" in text or "(QDialog)" in text:
                errors.append(f"QDialog usage must be explicitly allowlisted or converted to DocumentTab: {rel_path}")


def guard_document_bridges(errors: list[str]) -> None:
    bridge = (ROOT / "alrajhi_client/features/dialog_documents/dialog_document_tab.py").read_text(encoding="utf-8")
    for token in ("BaseDocumentTab", "workspace_save", "workspace_print", "workspace_export", "set_dirty"):
        if token not in bridge:
            errors.append(f"DialogDocumentTab bridge missing document command: {token}")

    # These widgets should delegate to workspace documents, not instantiate their old editors directly.
    widget_checks = {
        "alrajhi_client/views/widgets/invoices_widget.py": ["open_quick_invoice", "InvoiceDialog("],
        "alrajhi_client/views/widgets/customers_widget.py": ["open_party_document", "CustomerDialog("],
        "alrajhi_client/views/widgets/suppliers_widget.py": ["open_party_document", "SupplierDialog("],
        "alrajhi_client/views/widgets/categories_widget.py": ["open_category_document", "CategoryDialog("],
        "alrajhi_client/views/widgets/items_widget.py": ["open_item_document", "ItemDialog("],
    }
    for file_name, (required, banned) in widget_checks.items():
        p = ROOT / file_name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        if required not in text:
            errors.append(f"{file_name} must delegate to workspace hook {required}")
        if banned in text:
            errors.append(f"{file_name} must not directly instantiate legacy dialog {banned}")


def main() -> int:
    errors: list[str] = []
    parse_all(errors)
    guard_required_wiring(errors)
    guard_large_files(errors)
    guard_dialog_policy(errors)
    guard_document_bridges(errors)
    if errors:
        print("Phase 54 UI consistency guard failed:")
        for error in errors:
            print(f" - {error}")
        return 1
    print("Phase 54 UI consistency guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
