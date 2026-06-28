# -*- coding: utf-8 -*-
"""Phase417 legacy transaction quarantine boundary.

This module intentionally has no PyQt dependency.  It is imported before any
legacy dialog imports so accidental production imports fail with a deterministic
error instead of silently reactivating old event filters, row lifecycle code, or
fixed-column invoice/return grids.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Sequence


class LegacyTransactionQuarantineError(RuntimeError):
    """Raised when a quarantined transaction dialog is imported at runtime."""


@dataclass(frozen=True)
class LegacyTransactionModule:
    module: str
    path: str
    reason: str


QUARANTINED_TRANSACTION_MODULES: Sequence[LegacyTransactionModule] = (
    LegacyTransactionModule(
        module="features.invoices.invoice_editor_tab",
        path="alrajhi_client/features/invoices/invoice_editor_tab.py",
        reason="legacy InvoiceDialog adapter contains fixed-column navigation and old row lifecycle",
    ),
    LegacyTransactionModule(
        module="features.returns.return_editor_tabs",
        path="alrajhi_client/features/returns/return_editor_tabs.py",
        reason="legacy return dialogs reuse old Qt dialog controls outside the unified transaction shell",
    ),
    LegacyTransactionModule(
        module="views.dialogs.invoice_dialog",
        path="alrajhi_client/views/dialogs/invoice_dialog.py",
        reason="legacy invoice dialog owns local Enter handling and LinesModel row creation",
    ),
)

# This environment variable is deliberately long and forensic-only. It is not
# read by feature_flags.allow_legacy_transaction_documents(), and production
# navigation never enables it. It only lets a developer inspect a quarantined
# module manually during migration work.
FORENSIC_IMPORT_ENV = "ALRAJHI_FORENSIC_ALLOW_LEGACY_TRANSACTION_IMPORT"


def quarantined_module_names() -> tuple[str, ...]:
    return tuple(item.module for item in QUARANTINED_TRANSACTION_MODULES)


def is_quarantined_transaction_module(module_name: str) -> bool:
    normalized = module_name.removeprefix("alrajhi_client.")
    return any(
        normalized == item.module or normalized.endswith("." + item.module)
        for item in QUARANTINED_TRANSACTION_MODULES
    )


def forensic_legacy_import_enabled() -> bool:
    return os.environ.get(FORENSIC_IMPORT_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def assert_not_quarantined_transaction_module(module_name: str) -> None:
    if not is_quarantined_transaction_module(module_name):
        return
    if forensic_legacy_import_enabled():
        return
    raise LegacyTransactionQuarantineError(
        f"Legacy transaction module '{module_name}' is quarantined by Phase417. "
        "Use features.transactions.documents.* and TransactionDocumentTab instead."
    )


def scan_text_for_forbidden_legacy_imports(text: str) -> tuple[str, ...]:
    """Return forbidden production import fragments found in source text."""
    forbidden = (
        "from features.invoices import InvoiceEditorTab",
        "from features.invoices.invoice_editor_tab import",
        "import features.invoices.invoice_editor_tab",
        "from features.returns import SalesReturnEditorTab",
        "from features.returns import PurchaseReturnEditorTab",
        "from features.returns.return_editor_tabs import",
        "import features.returns.return_editor_tabs",
    )
    return tuple(fragment for fragment in forbidden if fragment in text)


def describe_quarantine() -> dict[str, object]:
    return {
        "phase": 417,
        "policy": "legacy_transaction_quarantine",
        "forensic_import_env": FORENSIC_IMPORT_ENV,
        "modules": [item.__dict__.copy() for item in QUARANTINED_TRANSACTION_MODULES],
    }


__all__ = [
    "FORENSIC_IMPORT_ENV",
    "LegacyTransactionModule",
    "LegacyTransactionQuarantineError",
    "QUARANTINED_TRANSACTION_MODULES",
    "assert_not_quarantined_transaction_module",
    "describe_quarantine",
    "forensic_legacy_import_enabled",
    "is_quarantined_transaction_module",
    "quarantined_module_names",
    "scan_text_for_forbidden_legacy_imports",
]
