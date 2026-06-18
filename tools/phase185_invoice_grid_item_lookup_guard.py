# -*- coding: utf-8 -*-
"""Phase 185 guard: invoice-grid material cell lookup must be case-insensitive.

This guard protects the exact bug reported by the user: typing a material name
inside the invoice line-grid item cell must resolve the material even if letter
case differs.  It also checks the legacy InvoiceDialog fallback delegate.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

checks = []

def require(path: str, needle: str, label: str) -> None:
    text = (ROOT / path).read_text(encoding='utf-8')
    if needle not in text:
        raise SystemExit(f"Missing {label} in {path}")
    checks.append(label)

require('alrajhi_client/features/transactions/grids/transaction_item_delegate.py', 'class TransactionItemDelegate', 'transaction item delegate')
require('alrajhi_client/features/transactions/grids/transaction_item_delegate.py', 'setCaseSensitivity(Qt.CaseInsensitive)', 'case-insensitive transaction completer')
require('alrajhi_client/features/transactions/grids/transaction_item_delegate.py', 'setFilterMode(Qt.MatchContains)', 'contains-match transaction completer')
require('alrajhi_client/features/transactions/grids/transaction_item_delegate.py', 'barcode_input_service.lookup_entry(text, mode="auto")', 'cell text lookup through unified barcode/manual service')
require('alrajhi_client/features/transactions/grids/transaction_line_grid.py', 'TransactionItemDelegate', 'TransactionLineGrid installs item delegate')
require('alrajhi_client/features/transactions/grids/transaction_line_grid.py', 'configure_item_delegate', 'delegate configuration hook')
require('alrajhi_client/features/transactions/grids/transaction_line_model.py', 'def set_item', 'model set_item for existing row')
require('alrajhi_client/features/transactions/transaction_document_tab.py', 'self.grid.configure_item_delegate', 'document configures item delegate')
require('alrajhi_client/features/transactions/transaction_document_tab.py', 'def _material_lookup_rows', 'document item provider')
require('alrajhi_client/views/dialogs/invoice_delegates.py', '_item_matches_text', 'legacy casefold matching helper')
require('alrajhi_client/views/dialogs/invoice_delegates.py', 'setCaseSensitivity(Qt.CaseInsensitive)', 'legacy case-insensitive completer')
require('alrajhi_client/views/dialogs/invoice_delegates.py', 'setFilterMode(Qt.MatchContains)', 'legacy contains-match completer')

# Guard against reintroducing the Phase 184 double-add regression in quick search.
text = (ROOT / 'alrajhi_client/features/transactions/transaction_document_tab.py').read_text(encoding='utf-8')
if text.count('self.lines_model.add_item(item, self._line_price_key(), warehouse_available=available)') != 1:
    raise SystemExit('Quick search must add the material exactly once')

print('phase185_invoice_grid_item_lookup_guard passed:', ', '.join(checks))
