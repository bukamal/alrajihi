# Phase 386 — Editable Grid Invoice Enter Route

## Goal

Rebuild invoice line Enter traversal around the operator's business sequence rather than physical column order.

## Contract

Purchase invoice line entry follows:

`المادة → الوحدة → الكمية → السعر → الخصم → الضريبة → الإجمالي → الملاحظات`

The database/model key remains `cost` for purchase accounting compatibility, but the visible purchase column label is now the same operator-facing `transaction_column_price` label used by sales.

Sales invoice line entry follows:

`المادة → الوحدة → الكمية → السعر → الخصم → الإجمالي → الملاحظات`

Tax is skipped in the sales fast-entry route. Hidden columns are skipped automatically. Read-only `total` is still focusable for visual confirmation, then Enter continues to notes or the next line.

## Runtime behavior

- Enter opens the editor on editable cells.
- Enter inside the editor commits the value and moves to the next business-route cell.
- Enter navigation does not clear or empty existing values.
- Editor text is selected for replacement only when the operator starts typing.
- Purchase batch/expiry remain accessible by mouse/Tab/column navigation, but are skipped by the fast Enter route.

## Verification

- `tools/phase386_editable_grid_invoice_enter_route_guard.py`
- `tests/test_phase386_editable_grid_invoice_enter_route.py`
