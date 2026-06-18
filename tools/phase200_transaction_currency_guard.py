#!/usr/bin/env python3
"""Phase 200 guard: transaction documents must honor display currency.

Purchase/sales invoices entered in the new TransactionDocumentTab display prices
in the active UI currency and persist them in the system base currency.  This
prevents the regression where purchase invoice cells showed raw USD values while
settings displayed another currency.
"""
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TAB = ROOT / "alrajhi_client/features/transactions/transaction_document_tab.py"
PANEL = ROOT / "alrajhi_client/features/transactions/components/transaction_totals_panel.py"
DELEGATE = ROOT / "alrajhi_client/features/transactions/grids/transaction_item_delegate.py"
GRID = ROOT / "alrajhi_client/features/transactions/grids/transaction_line_grid.py"
PRINT = ROOT / "alrajhi_client/features/transactions/components/transaction_printing_bridge.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    tab = TAB.read_text(encoding="utf-8")
    panel = PANEL.read_text(encoding="utf-8")
    delegate = DELEGATE.read_text(encoding="utf-8")
    grid = GRID.read_text(encoding="utf-8")
    printing = PRINT.read_text(encoding="utf-8")

    require("from currency import currency" in tab, "TransactionDocumentTab must use the currency manager.")
    require("self.display_currency = currency.get_display_currency()" in tab, "TransactionDocumentTab must capture active display currency.")
    require("def _to_display_money" in tab and "currency.convert(value or 0, self.storage_currency, self.display_currency)" in tab,
            "TransactionDocumentTab must convert stored/base amounts to display currency.")
    require("def _to_storage_money" in tab and "currency.convert(value or 0, self.display_currency, self.storage_currency)" in tab,
            "TransactionDocumentTab must convert UI/display amounts back to storage currency.")
    require("self._item_prices_to_display(item)" in tab, "Quick-search scanned items must be converted before entering invoice grid.")
    require("return [self._item_prices_to_display(row) for row in rows]" in tab,
            "Invoice item-cell completer rows must be display-currency converted.")
    require("self._invoice_lines_to_display(invoice.get(\"lines\")" in tab,
            "Loaded invoice lines must be converted to display currency.")
    require("self._invoice_lines_to_storage(self.lines_model.get_lines_data())" in tab,
            "Saved invoice lines must be converted back to storage currency.")
    require("\"original_currency\": self.display_currency" in tab,
            "Invoices/returns must persist the active display currency.")
    require('"original_currency": "USD"' not in tab,
            "TransactionDocumentTab must not hard-code original_currency to USD.")
    require("set_currency" in panel and "currency.format_amount" in panel,
            "Totals panel must format totals with the active display currency.")
    require("item_transform" in delegate and "self.item_transform(item)" in delegate,
            "Item-cell delegate must transform raw barcode lookup items before setting model data.")
    require("item_transform=self._item_transform" in grid,
            "TransactionLineGrid must pass the item transform into TransactionItemDelegate.")
    require("\"currency\": getattr(self.host, \"display_currency\"" in printing,
            "Transaction printing payloads must carry display currency metadata.")
    require("for row in self.lines_model.lines:\n            for row in self.lines_model.lines:" not in tab,
            "Duplicate validation loop detected in TransactionDocumentTab.")
    print("Phase 200 transaction currency guard passed.")


if __name__ == "__main__":
    main()
