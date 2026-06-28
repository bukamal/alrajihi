# -*- coding: utf-8 -*-
from __future__ import annotations

LEGACY_TRANSACTION_QUARANTINE_CONTRACT = {
    "phase": 417,
    "name": "legacy_transaction_quarantine",
    "scope": [
        "features.invoices.invoice_editor_tab",
        "features.returns.return_editor_tabs",
        "views.main_window transaction routing",
        "workspace.quality.legacy_transaction_quarantine",
    ],
    "requirements": [
        "Production navigation must not import legacy invoice or return adapters.",
        "Legacy adapters must raise before loading PyQt dialog classes unless forensic import is explicitly enabled.",
        "allow_legacy_transaction_documents remains false and is not used as a fallback in main_window.",
        "Direct package exports for legacy transaction adapters remain empty.",
        "The unified documents under features.transactions.documents are the only production transaction editors.",
    ],
    "forensic_only_env": "ALRAJHI_FORENSIC_ALLOW_LEGACY_TRANSACTION_IMPORT",
    "quarantined_modules": [
        "features.invoices.invoice_editor_tab",
        "features.returns.return_editor_tabs",
        "views.dialogs.invoice_dialog",
    ],
}

__all__ = ["LEGACY_TRANSACTION_QUARANTINE_CONTRACT"]
