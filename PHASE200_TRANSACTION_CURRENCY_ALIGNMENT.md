# Phase 200 — Transaction Currency Alignment

## Purpose

Fix the regression where the unified transaction invoice grid, especially purchase invoices, did not respect the active display currency.  The old `InvoiceDialog` converted prices from stored USD/base values into the selected display currency, but the new `TransactionDocumentTab` was still showing raw stored values and saving `original_currency = "USD"`.

## Changes

- `TransactionDocumentTab` now captures the active display currency using `currency.get_display_currency()`.
- Invoice and return lines loaded from storage are converted from system storage currency (`USD`) into the active display currency before entering the grid.
- Material rows resolved through quick search, completers, or barcode/unit-barcode lookup are converted to display currency before `TransactionLineModel.set_item()`.
- Invoice and return payloads convert UI/display amounts back to storage currency before save.
- `original_currency` now stores the active display currency instead of hard-coded `USD`.
- `exchange_rate_to_usd` now stores the current rate for the active display currency.
- `TransactionTotalsPanel` now formats totals and the paid field with the active display currency symbol.
- `TransactionItemDelegate` now accepts an `item_transform` callback, so raw barcode lookup results inside the grid cell are also display-currency converted.
- Transaction printing payloads now carry `currency`, `original_currency`, and `exchange_rate_to_usd` metadata.

## Scope

This specifically fixes:

- Purchase invoice grid item/cost entry.
- Sales invoice grid item/price entry.
- Existing invoice reload/edit mode.
- Sales/purchase returns loaded from original invoice lines.
- Quick-search and item-cell delegate entry paths.
- Barcode and unit-barcode item resolution inside transaction grids.

POS already keeps storage amounts internally and converts for display in its widget/model; this phase leaves that architecture intact.

## Guard

Added:

```text
tools/phase200_transaction_currency_guard.py
```

The guard prevents reintroducing:

- hard-coded `original_currency = "USD"` inside `TransactionDocumentTab`,
- raw item prices entering the transaction grid,
- missing display-to-storage conversion before save,
- missing currency formatting in totals,
- delegate bypass of display-currency conversion.

## Validation

Executed successfully:

```text
python tools/phase200_transaction_currency_guard.py
python tools/phase198_startup_circular_import_guard.py
python tools/phase199_startup_import_boundary_guard.py
python tools/phase197_inventory_printing_bridge_guard.py
python -m compileall -q alrajhi_client alrajhi_server
```
