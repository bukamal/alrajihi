# UNIT CONVERSION ADVANCED TEST REPORT

## Scope
Advanced headless validation for base/sub-units and their effects on invoices, prices, stock movements, returns, warehouse balances, and Inventory Ledger dual-read.

## Test item
- Base unit: `Piece`
- Sub-unit 1: `Box`, conversion factor = `12 Piece`
- Sub-unit 2: `Pack`, conversion factor = `6 Piece`

## Executed scenario
1. Created customer, supplier, category, item.
2. Added sub-units `Box` and `Pack`.
3. Purchase invoice: `2 Box × 120`.
   - Expected display quantity: `2 Box`.
   - Expected base quantity: `24 Piece`.
   - Expected stock delta: `+24`.
4. Sale invoice: `1 Pack × 90`.
   - Expected display quantity: `1 Pack`.
   - Expected base quantity: `6 Piece`.
   - Expected stock delta: `-6`.
5. Purchase invoice without explicit `base_qty`: `1 Box × 120`.
   - Expected fallback: `base_qty = quantity × conversion_factor = 12`.
6. Sales return from `1 Pack` sale.
   - Expected return display quantity: `1 Pack`.
   - Expected base return quantity: `6 Piece`.
   - Expected stock delta: `+6`.
7. Purchase return from `2 Box` purchase.
   - Expected return display quantity: `1 Box`.
   - Expected base return quantity: `12 Piece`.
   - Expected stock delta: `-12`.
8. Invoice edit/delete with units:
   - Created purchase `1 Box` = `12 Piece`.
   - Updated to `2 Pack` = `12 Piece`.
   - Deleted invoice.
   - Expected final stock returns to pre-invoice value.
9. Dual-read reconciliation:
   - Operational item quantity vs Inventory Ledger quantity.
   - Warehouse balance vs warehouse-level Ledger quantity.

## Findings fixed

### 1. Missing `base_qty` fallback
Some callers could send `quantity` and `conversion_factor` without `base_qty`. The old fallback treated display quantity as base quantity.

Fixed in:
- `alrajhi_client/database/connection.py`
- `alrajhi_server/api/invoices.py`
- `alrajhi_client/core/services/warehouse_service.py`

New behavior:
```text
base_qty = quantity × conversion_factor
```
when `base_qty` / `quantity_in_base` is not provided.

### 2. Returns used base quantity with display-unit price
Returnable lines exposed `returnable_qty` in base units while keeping `unit_price` from the invoice display unit. This caused wrong return totals and wrong stock effects for sub-units.

Fixed in:
- `alrajhi_client/gateways/local/sales_return_gateway.py`
- `alrajhi_client/gateways/local/purchase_return_gateway.py`
- `alrajhi_server/api/returns.py`

New behavior:
- `returnable_qty` is shown in the invoice unit.
- `returnable_qty_base` is retained for validation/diagnostics.
- Return creation converts entered display quantity back to base quantity.

### 3. Invoice edit/delete over-reversed warehouse movements
When an invoice was edited and then deleted, old warehouse movements could be reversed twice because the reverse operation did not net prior reversals.

Fixed in:
- `alrajhi_client/database/repositories/warehouse_repo.py`

New behavior:
- Warehouse reversal aggregates original and reverse movements by reference.
- Only the current net effect is reversed.

## Final test result
```text
setup_database_login: PASS
create_item_with_base_and_subunits: PASS
invoice_base_subunit_price_stock_effects: PASS
invoice_missing_base_qty_computes_from_conversion_factor: PASS
returns_use_invoice_unit_for_price_and_base_for_stock: PASS
invoice_update_delete_preserve_unit_base_stock_effects: PASS
ledger_dual_read_callable_after_unit_flows: PASS, mismatched = 0
static_ui_command_unit_conversion_compatibility: PASS
architecture_guard: PASS
compileall: PASS
AST syntax check: PASS
```

## Conclusion
The base/sub-unit flow is now consistent across:
- Invoice UI payloads
- Local invoice persistence
- Server invoice API
- Sales returns
- Purchase returns
- Warehouse movements
- Inventory Ledger dual-read

The tested unit behavior is production-safe for the covered paths, subject to live PyQt UI confirmation on a real desktop environment.
