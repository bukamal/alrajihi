# Migration / Database Schema Unification

## Applied changes

1. Added a shared idempotent schema guard:
   - `alrajhi_client/database/schema_manager.py`
   - `alrajhi_server/database/schema_manager.py`

2. Wired the schema guard into both migration entry points:
   - `alrajhi_client/database/migrations.py`
   - `alrajhi_server/database/migrations.py`

3. The guard automatically creates/updates shared operational tables when missing:
   - `schema_migrations`
   - `branches`
   - `warehouses`
   - `cashboxes`
   - `bank_accounts`
   - `cash_bank_movements`
   - `pos_shifts`
   - `item_warehouse_balances`
   - `warehouse_movements`
   - `warehouse_transfers`

4. The guard automatically adds missing columns to old databases, including:
   - `invoices.warehouse_id`
   - `invoices.branch_id`
   - `invoices.cashbox_id`
   - `invoices.bank_account_id`
   - `invoices.payment_method`
   - `invoices.shift_id`
   - corresponding branch/cash/bank/payment columns for `vouchers` and `expenses`

5. Added migration tracking:
   - `schema_migrations.version = 20260611`
   - `PRAGMA user_version = 20260611`

## Main fixed issue

Old existing SQLite databases that were created before adding warehouse/cashbox/branch support will now be upgraded at startup instead of failing with errors such as:

```text
table invoices has no column named warehouse_id
```

or similar missing-column errors.

## Validation

- Python compilation passed for client and server modules.
- A simulated old SQLite database was upgraded successfully.
- Verified that missing columns were added correctly to `invoices`, `vouchers`, `expenses`, and operational tables.
