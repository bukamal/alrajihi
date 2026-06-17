# Phase126 — Schema Reinitialization Hotfix

## Problem
Reset/reinitialization rejected valid Alrajhi SQLite databases with:

- `النسخة لا تبدو قاعدة الراجحي`
- `جداول ناقصة: Inventory_movements`
- `no such table: inventory_ledger`

## Root cause
1. Backup/reset validation treated versioned tables as mandatory identity tables.
2. The check compared table names case-sensitively while SQLite table lookup is effectively case-insensitive.
3. `schema_manager.apply_common_schema()` created `inventory_ledger` but did not create/repair legacy `inventory_movements`.
4. Old databases containing `Inventory_movements` with non-standard casing or incomplete columns were not upgraded correctly.

## Fix
- Added `inventory_movements` to the shared schema guard for client and server.
- Added idempotent column repair for old `inventory_movements` tables.
- Made schema table detection case-insensitive.
- Changed backup/reset validation to check only identity tables: `users`, `items`, `invoices`, `vouchers`.
- Restore now upgrades schema on the copied temporary DB before replacing the active database.
- Backup creation upgrades the live local database before creating the backup.

## Tests
- `compileall`: PASS
- Case-insensitive `Inventory_movements` upgrade test: PASS
- `inventory_ledger` creation test: PASS
- Backup gateway schema restore test with PyQt mock: PASS

## Expected result
Reset/restore should no longer fail just because `Inventory_movements` / `inventory_movements` or `inventory_ledger` is missing in an older database. The schema guard creates or repairs those tables automatically.
