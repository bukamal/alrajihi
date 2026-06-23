# Phase 349 — Transaction Entry, Cash Party & Footer Polish

This phase unifies three operator-facing transaction behaviors across invoice-like screens.

## Scope

- Editable grids visually mark the active cell/field.
- Saving sales/purchase/return documents without selecting a customer or supplier is treated as a valid cash/counter document.
- Transaction footer summaries and bottom action buttons use central typography, spacing, and button sizing.

## Contract

- `StandardTableKeyboardMixin` exposes `standard_table_keyboard` and `current_cell_highlight` properties and keeps the current editable cell selected.
- Global QSS paints the current cell/editor through theme tokens.
- `TransactionDocumentTab` defaults the party row to `payment_cash` and does not show a blocking no-party confirmation.
- Footer/payment labels and bottom actions expose object names/properties so all similar transaction surfaces receive the same visual treatment.

## Guard

Run:

```bash
python tools/phase349_transaction_entry_cash_footer_guard.py
```

Outputs:

- `tools/audit_outputs/transaction_entry_cash_footer_matrix.csv`
- `tools/audit_outputs/transaction_entry_cash_footer_summary.json`
