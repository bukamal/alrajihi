# Phase 185 — Invoice Grid Item Cell Lookup

## Problem
Phase 184 fixed case-insensitive material lookup for the quick search field and the local/API catalog search path, but the user clarified that the issue is inside the invoice line grid itself: the `المادة` / item-name cell in sales and purchase invoice creation.

## Fix
This phase adds a real item-cell delegate to the new transaction invoice grid and hardens the legacy invoice dialog fallback.

### New transaction grid
- Added `features/transactions/grids/transaction_item_delegate.py`.
- `TransactionLineGrid` now installs `TransactionItemDelegate` on the `item` column.
- `TransactionDocumentTab` passes material providers, price mode, and warehouse availability to the delegate.
- `TransactionLineModel` now exposes `set_item(row, item, ...)` so the delegate can resolve the typed material into an existing row instead of writing plain text only.
- The delegate uses the unified `barcode_input_service.lookup_entry(..., mode="auto")`:
  - manual material names are case-insensitive,
  - scanner-like barcodes remain exact,
  - unit barcode metadata is preserved.

### Legacy fallback
- Hardened `views/dialogs/invoice_delegates.py`:
  - `QCompleter` is case-insensitive,
  - completion supports `Qt.MatchContains`,
  - typed material name/barcode/code is matched with `.casefold()`,
  - fallback does not require exact letter case.

### Regression fixed
- Confirmed quick-search `add_item_from_search()` adds the material only once.

## Guard
Added:

```text
tools/phase185_invoice_grid_item_lookup_guard.py
```

It checks that both the new transaction grid and the legacy invoice dialog support case-insensitive item-cell lookup and that the duplicate quick-search add regression is not present.
