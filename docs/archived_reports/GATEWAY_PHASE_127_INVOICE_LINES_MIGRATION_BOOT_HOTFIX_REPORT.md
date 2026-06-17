# Phase127 - Invoice Lines Migration Boot Hotfix

## Problem
Startup failed during local database initialization:

```text
sqlite3.OperationalError: no such table: invoice_lines
```

The migration attempted to alter `invoice_lines` before safely ensuring that the table exists. In addition, the base `CREATE TABLE invoice_lines` definition contained a duplicated `conversion_factor` column declaration, which could stop schema creation and leave a partially initialized database.

## Fix
- Removed the duplicate `conversion_factor` declaration from the base `invoice_lines` schema.
- Added a table-existence guard before `ALTER TABLE invoice_lines`.
- If `invoice_lines` is missing in an older/partially-created database, it is created safely first.
- Existing databases still receive the `conversion_factor` column if it is missing.

## Validation
- `py_compile` passed for `alrajhi_client/database/migrations.py`.
- Schema path is now idempotent for fresh and partially initialized SQLite databases.
