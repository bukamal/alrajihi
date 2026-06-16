# Phase128 Migration Order Hotfix

## Problem
Startup failed on existing/partially initialized local databases because `ensure_db()` ran legacy `ALTER TABLE` migrations before guaranteeing the base schema existed. After `invoice_lines`, the same pattern failed on `production_orders`:

```text
sqlite3.OperationalError: no such table: production_orders
```

## Root Cause
The database file existed, so `ensure_db()` skipped `init_database()` and immediately executed schema upgrades. If the DB file was empty/partial/older/restored, core tables such as `invoice_lines` or `production_orders` did not exist yet.

## Fix
- Bootstrap core schema with `CREATE TABLE IF NOT EXISTS` before legacy ALTER migrations even when the DB file already exists.
- Added case-insensitive table existence helper.
- Added guarded column helper `_add_column_if_missing()`.
- Guarded `production_orders` migration columns:
  - `linked_entry_id`
  - `linked_entry_type`
  - `raw_warehouse_id`
  - `output_warehouse_id`
- Guarded currency columns for invoices/vouchers/expenses.

## Verification
- `python3 -m py_compile alrajhi_client/database/migrations.py` passed.
- `python3 -m compileall -q alrajhi_client/database/migrations.py` passed.

## Expected Result
Starting the application on an old, restored, or partially created DB should no longer crash at `ALTER TABLE production_orders` or `invoice_lines`; the base schema is created first, then migrations run.
