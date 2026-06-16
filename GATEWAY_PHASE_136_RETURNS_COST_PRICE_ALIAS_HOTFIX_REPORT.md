# Phase136 - Returns cost_price alias hotfix

## Issue
Opening return dialogs failed with:

`no such column: It.cost_price`

The local SQLite `items` table defines `purchase_price`, `selling_price`, and `average_cost`, but not `cost_price`.

## Fix
Updated `alrajhi_client/database/connection.py` in `get_invoice_by_id()`:

- Removed direct reference to missing `it.cost_price`.
- Added compatible alias:
  `COALESCE(it.average_cost, it.purchase_price, '0') AS item_cost_price`

This keeps downstream return/invoice UI code compatible without adding a fake schema column.

## Tests
- `compileall` for modified file and returns widget.
- SQLite guard with an `items` table that does not contain `cost_price`.

Result: PASS.
