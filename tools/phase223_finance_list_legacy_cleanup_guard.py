#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard for Phase 223 finance list legacy cleanup.

Ensures finance listing widgets no longer carry their own large modal editor
implementations after the document-shell migration. Primary create/edit flows
must route to MainWindow document openers.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKS = {
    "alrajhi_client/views/widgets/vouchers_widget.py": {
        "forbidden": ["class VoucherDialog", "VoucherDialog(", ".exec_()", ".exec()", "QDialog", "QDialogButtonBox"],
        "required": ["open_quick_voucher", "currency.format_base_amount", "cannot_open_document_tab"],
    },
    "alrajhi_client/views/widgets/cashboxes_widget.py": {
        "forbidden": ["class CashboxDialog", "class BankDialog", "CashboxDialog(", "BankDialog(", ".exec_()", ".exec()", "QDialog", "QDialogButtonBox"],
        "required": ["open_cashbox_document", "open_bank_account_document", "cannot_open_document_tab"],
    },
}


def main() -> int:
    errors: list[str] = []
    for rel, cfg in CHECKS.items():
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        for token in cfg["forbidden"]:
            if token in text:
                errors.append(f"{rel}: forbidden legacy/modal token remains: {token}")
        for token in cfg["required"]:
            if token not in text:
                errors.append(f"{rel}: required document-routing token missing: {token}")
    if errors:
        for error in errors:
            print("ERROR:", error)
        return 1
    print("phase223_finance_list_legacy_cleanup_guard: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
