# Returns System Fix Phase 101

Scope: sales returns and purchase returns across server API, local/remote command paths, stock ledger, warehouse balance, cash/bank movement, and UI settlement payload.

## Fixed

1. Server return creation no longer builds tuple-based prepared lines and then reads them as dictionaries. Prepared lines now use one canonical dictionary shape aligned with local gateways.
2. Server purchase return creation now validates warehouse availability before posting a return.
3. Server default refund calculation now matches local gateways: refund defaults to the amount that must be paid back after applying the return against the remaining receivable/payable.
4. Server return creation now records warehouse movements and refreshes item warehouse balances in addition to legacy inventory_movements and inventory_ledger.
5. Server return creation now posts cash/bank movements for actual refunds, aligned with local cashbox semantics:
   - sales return refund: negative cash/bank amount, direction out;
   - purchase return refund: positive cash/bank amount, direction in.
6. Server return cancellation now reverses all affected layers:
   - inventory_movements;
   - warehouse_movements and item_warehouse_balances;
   - item quantity and average cost;
   - customer/supplier credit effect;
   - user cash balance;
   - cash_bank_movements reference rows;
   - append-only inventory_ledger reversal rows.
7. UI no longer rewrites `credit_only` settlement to `cash`; the selected command value is preserved.

## Verification

- `python3 -m compileall -q alrajhi_server alrajhi_client tools`
- `python3 tools/phase32_invoice_flow_guard.py`
- `python3 tools/verify_language_phase78_sales_purchases_returns.py`
- `python3 tools/verify_dialog_buttonbox_integrity.py`

All checks passed in the repair environment.
