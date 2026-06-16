# Phase 151 Startup Hotfix

## Problem
Application startup failed during `ensure_local_database()` with:

```text
sqlite3.OperationalError: no such column: workflow_status
```

## Root cause
`init_database()` is called for existing SQLite files. In SQLite, `CREATE TABLE IF NOT EXISTS invoices (...)` does not add newly introduced columns to an already existing table. The Phase 151 index:

```sql
CREATE INDEX IF NOT EXISTS idx_invoices_workflow_status ON invoices(workflow_status);
```

was created inside the initial `executescript()` before the safe `ALTER TABLE` migration added `workflow_status` to upgraded databases.

## Fix
Moved creation of `idx_invoices_workflow_status` out of the unsafe initial SQL script and added a safe Phase 151 column-enforcement block immediately after the script and before `apply_common_schema()`.

The migration now:

1. Ensures the `invoices` table exists.
2. Checks existing columns via `PRAGMA table_info(invoices)`.
3. Adds missing workflow columns with `ALTER TABLE`.
4. Creates `idx_invoices_workflow_status` only after `workflow_status` exists.

## Files changed

- `alrajhi_client/database/migrations.py`

## Expected result
The app should pass startup migration on both:

- new databases
- old/upgraded databases created before Phase 151
