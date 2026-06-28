# -*- coding: utf-8 -*-
"""Phase403 Basit-inspired invoice/return transaction surface contract."""
from __future__ import annotations

BASIT_TRANSACTION_SURFACE_CONTRACT = {
    "phase": 403,
    "surface": "transactions",
    "goal": "Apply the Basit-inspired operational grammar to sales/purchase invoices and returns.",
    "requirements": [
        "Transaction documents are tagged basitInspired and basitTransactionDocument.",
        "Inline invoice header uses the Basit toolbar colors and dimensions.",
        "Add/save/columns/reset/auto-responsive buttons use the Basit toolbar button role.",
        "Invoice and return line grids use the Basit table surface and row/header styling.",
        "Footer totals and payment frames use Basit panel/total visual roles.",
        "Net total is emphasized using the red Basit total badge.",
    ],
    "tokens": [
        "basit_blue", "basit_yellow", "basit_red", "basit_table_bg", "basit_toolbar_height", "basit_total_height",
    ],
}
