#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "audit_outputs"
OUT_CSV = OUT_DIR / "legacy_elimination_foundation_matrix.csv"


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _function_body(src: str, name: str) -> str:
    match = re.search(rf"def {re.escape(name)}\([^)]*\)(?:\s*->\s*[^:]+)?:([\s\S]*?)(?:\ndef |\nclass |\Z)", src, flags=re.S)
    return match.group(1) if match else ""


def _py_files():
    return [p for p in (ROOT / "alrajhi_client").rglob("*.py")]


def main() -> int:
    rows: list[dict[str, str]] = []

    def add(check: str, category: str, ok: bool, detail: str, path: str = ""):
        rows.append({
            "check": check,
            "category": category,
            "path": path,
            "status": "OK" if ok else "FAIL",
            "detail": detail,
        })

    main_window = read("alrajhi_client/views/main_window.py")
    qss = read("alrajhi_client/theme/qss.py")
    flags = read("alrajhi_client/features/transactions/feature_flags.py")
    invoices_init = read("alrajhi_client/features/invoices/__init__.py")
    returns_init = read("alrajhi_client/features/returns/__init__.py")

    add("phase_doc", "doc", "PHASE414_LEGACY_ELIMINATION_FOUNDATION.md" in {p.name for p in ROOT.glob("PHASE414_*.md")}, "phase document exists", "PHASE414_LEGACY_ELIMINATION_FOUNDATION.md")
    add("contract", "contract", "LEGACY_ELIMINATION_CONTRACT" in read("alrajhi_client/workspace/quality/legacy_elimination_contract.py"), "contract exists", "alrajhi_client/workspace/quality/legacy_elimination_contract.py")

    required_main = {
        "clean_shell_class": "class CleanShellNavigationBar(QFrame)",
        "clean_shell_instance": "self.menu_bar = CleanShellNavigationBar(self)",
        "non_visual_topbar_adapter": "self.top_bar = ShellCompatibilityAdapter()",
        "manual_popup": "menu.popup(button.mapToGlobal",
        "push_button_nav": "button = QPushButton(self)",
        "clean_object_name": "CleanShellNavigationBar",
        "clean_button_object": "MainNavButton",
        "finish_rebuild": "self.menu_bar.finish_rebuild()",
    }
    for check, needle in required_main.items():
        add(check, "main_window", needle in main_window, f"requires {needle!r}", "alrajhi_client/views/main_window.py")

    banned_main = [
        "from views.modern_topbar import",
        "ModernTopBar(",
        "class IconMenuBar",
        "self.menu_bar = IconMenuBar",
        "QToolButton#MainNavToolButton",
        "btn.setMenu(menu)",
        "QToolButton.InstantPopup",
        "main_layout.addWidget(self.top_bar)",
        "from features.invoices import InvoiceEditorTab",
        "from features.returns import SalesReturnEditorTab",
        "from features.returns import PurchaseReturnEditorTab",
        "ReturnEditorTab =",
    ]
    for needle in banned_main:
        add(f"banned_main_{needle[:24].strip().replace(' ', '_')}", "main_window", needle not in main_window, f"forbid {needle!r}", "alrajhi_client/views/main_window.py")

    add("qss_clean_shell_selector", "theme", "QFrame#CleanShellNavigationBar" in qss, "global QSS styles the clean shell selector", "alrajhi_client/theme/qss.py")
    add("qss_clean_button_selector", "theme", "QPushButton#MainNavButton" in qss, "global QSS styles the clean nav button selector", "alrajhi_client/theme/qss.py")
    add("qss_no_old_main_nav_selector", "theme", "QToolButton#MainNavToolButton" not in qss, "old main nav QToolButton selector removed", "alrajhi_client/theme/qss.py")

    body = _function_body(flags, "allow_legacy_transaction_documents")
    add("legacy_flag_constant", "transactions", "LEGACY_TRANSACTION_DOCUMENTS_DISABLED = True" in flags, "legacy disable constant is present", "alrajhi_client/features/transactions/feature_flags.py")
    add("legacy_flag_false", "transactions", "return False" in body, "allow_legacy_transaction_documents returns False", "alrajhi_client/features/transactions/feature_flags.py")
    add("legacy_flag_no_env", "transactions", "os.environ" not in body and "settings_service" not in body, "legacy route cannot be re-enabled by env/settings", "alrajhi_client/features/transactions/feature_flags.py")

    add("invoice_package_no_legacy_export", "transactions", "InvoiceEditorTab" not in invoices_init and "__all__: list[str] = []" in invoices_init, "invoice package exports no legacy adapter", "alrajhi_client/features/invoices/__init__.py")
    add("returns_package_no_legacy_export", "transactions", "SalesReturnEditorTab" not in returns_init and "PurchaseReturnEditorTab" not in returns_init and "__all__: list[str] = []" in returns_init, "returns package exports no legacy adapter", "alrajhi_client/features/returns/__init__.py")

    invoice_dialog_imports = []
    for path in _py_files():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "from views.dialogs.invoice_dialog import" in text or "import views.dialogs.invoice_dialog" in text:
            invoice_dialog_imports.append(rel)
    allowed_invoice_imports = {"alrajhi_client/features/invoices/invoice_editor_tab.py"}
    add("invoice_dialog_imports_isolated", "transactions", set(invoice_dialog_imports) <= allowed_invoice_imports, f"imports={invoice_dialog_imports}", "alrajhi_client")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["check", "category", "path", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    failures = [row for row in rows if row["status"] != "OK"]
    if failures:
        print("Phase414 legacy elimination foundation failed:")
        for row in failures:
            print(f"- {row['check']}: {row['detail']}")
        return 1
    print(f"Phase414 legacy elimination foundation OK ({len(rows)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
