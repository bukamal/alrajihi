#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 65 guard: invoice-like transactions use the unified document UX.

The sales/purchase invoice surface must be a tab-friendly transaction document:
compact header, dominant transaction grid, protected required columns, responsive
splitter, and bottom actions.  This guard prevents regression to the narrow
legacy dialog/table pattern.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []

invoice = ROOT / "alrajhi_client" / "views" / "dialogs" / "invoice_dialog.py"
grid = ROOT / "alrajhi_client" / "features" / "transactions" / "grids" / "transaction_line_grid.py"
layout = ROOT / "alrajhi_client" / "features" / "transactions" / "components" / "transaction_document_layout.py"
hidden = ROOT / "build" / "pyinstaller_hidden_imports.py"

texts = {
    "invoice_dialog.py": invoice.read_text(encoding="utf-8"),
    "transaction_line_grid.py": grid.read_text(encoding="utf-8") if grid.exists() else "",
    "transaction_document_layout.py": layout.read_text(encoding="utf-8") if layout.exists() else "",
    "pyinstaller_hidden_imports.py": hidden.read_text(encoding="utf-8") if hidden.exists() else "",
}

required_invoice = {
    "TransactionLineGrid": "invoice lines must use the unified transaction grid",
    "TransactionDocumentLayout": "invoice tab must use the shared transaction document layout",
    "self.content_splitter = content_splitter": "invoice body splitter must be addressable and responsive",
    "self.bottom_action_bar = bottom_bar": "invoice actions must remain below the document body",
    "required_columns={LinesModel.COL_ITEM_NAME": "item column must be protected from hiding",
    "LinesModel.COL_QUANTITY, LinesModel.COL_UNIT, LinesModel.COL_TOTAL": "qty/unit/total must be protected from hiding",
    "self.title_frame = title_frame": "embedded tabs must be able to hide the legacy title card",
}
for token, msg in required_invoice.items():
    if token not in texts["invoice_dialog.py"]:
        errors.append(f"invoice_dialog.py: missing {msg}")

required_grid = {
    "class TransactionLineGrid": "TransactionLineGrid class",
    "def required_columns": "required-column API",
    "def apply_compact_preset": "compact responsive preset",
    "def apply_wide_preset": "wide responsive preset",
    "def fit_transaction_columns": "transaction-specific column fitting",
    "def setColumnHidden": "required-column hide protection",
}
for token, msg in required_grid.items():
    if token not in texts["transaction_line_grid.py"]:
        errors.append(f"transaction_line_grid.py: missing {msg}")

required_layout = {
    "class TransactionDocumentLayout": "TransactionDocumentLayout class",
    "title_frame.setVisible(False)": "legacy title-card hiding in embedded workspace tabs",
    "splitter.setStretchFactor(0, 7)": "line grid must dominate splitter space",
    "grid.setMinimumHeight(440)": "transaction line grid must be tall enough",
    "TransactionBottomActionBar": "bottom action-bar styling contract",
}
for token, msg in required_layout.items():
    if token not in texts["transaction_document_layout.py"]:
        errors.append(f"transaction_document_layout.py: missing {msg}")

for token in ("features.transactions", "features.transactions.grids.transaction_line_grid", "features.transactions.components.transaction_document_layout"):
    if token not in texts["pyinstaller_hidden_imports.py"]:
        errors.append(f"pyinstaller_hidden_imports.py: missing {token}")

if "title_layout.addWidget(self.save_btn)" in texts["invoice_dialog.py"] or "title_layout.addWidget(self.print_btn)" in texts["invoice_dialog.py"]:
    errors.append("invoice_dialog.py: save/print actions must not move back into the title/header bar")

if errors:
    print("Transaction document UX guard failed:")
    for err in errors:
        print(f" - {err}")
    sys.exit(1)
print("Transaction document UX guard passed.")
