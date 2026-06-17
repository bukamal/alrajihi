# Phase 108 - Invoice Deep Fixes

## Scope
Applied the four defects found in phase107 without changing project routes or command style:

1. Local invoice update must reject invoices linked to active returns.
2. Local invoice delete must reject invoices linked to active returns.
3. Server invoice create/update must persist payment metadata: `cashbox_id`, `bank_account_id`, `payment_method`, `shift_id`.
4. Server sale invoice create/update must validate available stock in base units before posting inventory movements.

## Modified files

- `alrajhi_client/database/connection.py`
- `alrajhi_server/api/invoices.py`
- `tools/invoice_phase108_integrity_guard.py`
- `test_reports/invoice_phase108_deep_fixes.md`

## Implementation details

### Local hard guard
Added `_invoice_has_returns(invoice_id)` checks inside local `update_invoice` and `delete_invoice`, next to the existing voucher guards. This prevents bypassing the UI/service layer and mutating invoices that already have sales/purchase returns.

### Server payment metadata
Expanded invoice INSERT and UPDATE statements to include:

- `cashbox_id`
- `bank_account_id`
- `payment_method`
- `shift_id`

This aligns remote invoice persistence with the local schema and voucher/cashbox flows.

### Server stock validation
Added `_available_item_quantity` and `_assert_sale_stock_available`.

For sale invoices, required quantities are aggregated per `item_id` in base units using:

`base_qty` if supplied, otherwise `quantity_in_base`, otherwise `quantity * conversion_factor`.

Create path validates before opening the transaction. Update path validates after reversing/deleting old invoice inventory movements, so editing an existing invoice does not falsely count its old sale movement against itself.

Validation failures return HTTP 400 with required and available quantities.

## Tests executed

- `python3 -m compileall -q alrajhi_client alrajhi_server tools`
- `python3 tools/phase32_invoice_flow_guard.py`
- `python3 tools/invoice_units_guard.py`
- `python3 tools/invoice_price_edit_deep_test_phase106.py`
- `python3 tools/vouchers_deep_accounting_test_phase105.py`
- `python3 tools/invoice_phase108_integrity_guard.py`

## Result

All executed guards passed.

Known limitation: full Flask route runtime execution was not performed in this container because Flask is not installed in the runtime environment. The server changes were compiled and statically guarded for route-level persistence/validation placement.
