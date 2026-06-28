#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tools" / "audit_outputs"
OUT_CSV = OUT_DIR / "legacy_transaction_quarantine_matrix.csv"


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _index_before(text: str, first: str, second: str) -> bool:
    a = text.find(first)
    b = text.find(second)
    return a >= 0 and b >= 0 and a < b


def main() -> int:
    rows: list[dict[str, str]] = []

    def add(check: str, category: str, ok: bool, detail: str, path: str = "") -> None:
        rows.append({
            "check": check,
            "category": category,
            "path": path,
            "status": "OK" if ok else "FAIL",
            "detail": detail,
        })

    doc = read("PHASE417_LEGACY_TRANSACTION_QUARANTINE.md")
    contract = read("alrajhi_client/workspace/quality/legacy_transaction_quarantine_contract.py")
    quarantine = read("alrajhi_client/workspace/quality/legacy_transaction_quarantine.py")
    main_window = read("alrajhi_client/views/main_window.py")
    flags = read("alrajhi_client/features/transactions/feature_flags.py")
    invoice_adapter = read("alrajhi_client/features/invoices/invoice_editor_tab.py")
    return_adapter = read("alrajhi_client/features/returns/return_editor_tabs.py")
    invoices_init = read("alrajhi_client/features/invoices/__init__.py")
    returns_init = read("alrajhi_client/features/returns/__init__.py")
    release_gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")

    add("phase_doc", "doc", "Phase 417" in doc and "Legacy Transaction Quarantine" in doc, "phase documentation exists", "PHASE417_LEGACY_TRANSACTION_QUARANTINE.md")
    add("contract", "contract", "LEGACY_TRANSACTION_QUARANTINE_CONTRACT" in contract and '"phase": 417' in contract, "contract exists and declares phase 417", "alrajhi_client/workspace/quality/legacy_transaction_quarantine_contract.py")

    required_quarantine = [
        "class LegacyTransactionQuarantineError",
        "QUARANTINED_TRANSACTION_MODULES",
        "FORENSIC_IMPORT_ENV",
        "ALRAJHI_FORENSIC_ALLOW_LEGACY_TRANSACTION_IMPORT",
        "assert_not_quarantined_transaction_module",
        "scan_text_for_forbidden_legacy_imports",
        "describe_quarantine",
    ]
    for needle in required_quarantine:
        add(f"quarantine_{needle[:28].replace(' ', '_')}", "quarantine", needle in quarantine, f"requires {needle!r}", "alrajhi_client/workspace/quality/legacy_transaction_quarantine.py")

    add("invoice_adapter_quarantined", "transactions", "QUARANTINED_LEGACY_TRANSACTION_MODULE = True" in invoice_adapter, "invoice legacy adapter marked quarantined", "alrajhi_client/features/invoices/invoice_editor_tab.py")
    add("invoice_quarantine_before_legacy_import", "transactions", _index_before(invoice_adapter, "assert_not_quarantined_transaction_module(__name__)", "from views.dialogs.invoice_dialog import InvoiceDialog"), "invoice adapter blocks before InvoiceDialog import", "alrajhi_client/features/invoices/invoice_editor_tab.py")
    add("return_adapter_quarantined", "transactions", "QUARANTINED_LEGACY_TRANSACTION_MODULE = True" in return_adapter, "return legacy adapters marked quarantined", "alrajhi_client/features/returns/return_editor_tabs.py")
    add("return_quarantine_before_pyqt_import", "transactions", _index_before(return_adapter, "assert_not_quarantined_transaction_module(__name__)", "from PyQt5.QtCore import"), "return adapter blocks before PyQt dialog import", "alrajhi_client/features/returns/return_editor_tabs.py")

    forbidden_main = [
        "from features.invoices import InvoiceEditorTab",
        "from features.invoices.invoice_editor_tab import",
        "from features.returns import SalesReturnEditorTab",
        "from features.returns import PurchaseReturnEditorTab",
        "from features.returns.return_editor_tabs import",
        "allow_legacy_transaction_documents,",
        "legacy_allowed = allow_legacy_transaction_documents",
    ]
    for needle in forbidden_main:
        add(f"main_no_{needle[:26].strip().replace(' ', '_')}", "main_window", needle not in main_window, f"forbid {needle!r}", "alrajhi_client/views/main_window.py")

    add("main_invoice_phase417_message", "main_window", "quarantined by Phase417" in main_window and "Legacy invoice dialog is disabled by Phase414" in main_window, "invoice fallback reports quarantine", "alrajhi_client/views/main_window.py")
    add("main_return_phase417_message", "main_window", "Legacy return dialog is disabled by Phase414 and quarantined by Phase417" in main_window, "return fallback reports quarantine", "alrajhi_client/views/main_window.py")

    add("legacy_flag_still_false", "transactions", "def allow_legacy_transaction_documents" in flags and "return False" in flags, "legacy flag remains hard false", "alrajhi_client/features/transactions/feature_flags.py")
    add("legacy_flag_mentions_quarantine", "transactions", "Phase417 also quarantines direct imports" in flags, "feature flag documents quarantine", "alrajhi_client/features/transactions/feature_flags.py")

    add("invoice_package_empty", "transactions", "__all__: list[str] = []" in invoices_init and "InvoiceEditorTab" not in invoices_init, "invoice package exports no legacy adapter", "alrajhi_client/features/invoices/__init__.py")
    add("returns_package_empty", "transactions", "__all__: list[str] = []" in returns_init and "SalesReturnEditorTab" not in returns_init and "PurchaseReturnEditorTab" not in returns_init, "returns package exports no legacy adapter", "alrajhi_client/features/returns/__init__.py")

    add("release_gate_registered", "release", "PHASE417_LEGACY_TRANSACTION_QUARANTINE" in release_gate and "phase417_legacy_transaction_quarantine_guard.py" in release_gate and "phase=417" in release_gate, "release gate knows phase 417", "alrajhi_client/workspace/quality/release_gate_contract.py")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["check", "category", "path", "status", "detail"])
        writer.writeheader()
        writer.writerows(rows)

    failures = [row for row in rows if row["status"] != "OK"]
    if failures:
        print("Phase417 legacy transaction quarantine failed:")
        for row in failures:
            print(f"- {row['check']}: {row['detail']}")
        return 1
    print(f"Phase417 legacy transaction quarantine OK ({len(rows)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
