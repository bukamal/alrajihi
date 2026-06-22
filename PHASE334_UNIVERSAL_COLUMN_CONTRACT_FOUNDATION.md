# Phase 334 — Universal Column Contract Foundation

This phase establishes the first central column contract for the unified UI work.

## Goals

- Define one PyQt-free `ColumnDefinition` contract for screen display, printing and export.
- Define one `TableColumnContract` per registered table.
- Start with the highest-risk tables: sales invoice lines, purchase invoice lines, returns and apparel variants/reports.
- Give each column stable settings keys under `ui/columns/<page>/<table>/<column>`.
- Preserve existing visible-column behavior while making print/export read dedicated column flags.

## Implemented

- Added `workspace/tables/column_contract.py`.
- Added `workspace/tables/table_column_registry.py`.
- Added public exports in `workspace/tables/__init__.py`.
- Added transaction schema bridge helpers:
  - `universal_contract_for_document(document_type)`
  - `universal_columns_for_document(document_type)`
  - `TransactionColumn.to_column_definition(...)`
- Bound `TransactionDocumentTab` line grids to the contract for sales, purchase and returns.
- Bound the apparel variants table to the `apparel.variants` column contract.
- Extended `CustomTableView` so print/export can filter columns by `printable_default` and `exportable_default` while display still respects user visibility.

## Guarded behavior

- Required invoice columns remain required.
- Apparel variant columns include item/color/size/variant code/barcode/quantity/reorder/sale price/status.
- The internal field may still be named `sku`, but the user-facing label is the existing translated variant-code label, not a visible `SKU` term.
- Printing/export now has its own contract flags, preparing Phase 336 for full print/export column mapping.

## Next phase

Phase 335 should extend this contract to restaurant, cafe, POS and operational tables before Phase 336 makes all print templates consume the same contract.
