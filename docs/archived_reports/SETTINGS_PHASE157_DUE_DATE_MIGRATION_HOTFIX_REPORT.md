# Phase 157 due_date migration hotfix

## Problem
Startup failed with:

```text
sqlite3.OperationalError: duplicate column name: due_date
```

## Cause
The local client migration attempted to add `due_date` twice in the same safe ALTER loop. Because the in-memory column set was not refreshed after the first `ALTER TABLE`, the second loop item attempted to add the same column again.

## Fix
- Removed the duplicate `due_date` entry from the client invoice migration loop.
- Updated the client migration to add newly created columns to the local `invoice_columns` set immediately after `ALTER TABLE`.
- Applied the same set-refresh safety pattern to the server migration.
- Re-ran `compileall` for `alrajhi_client` and `alrajhi_server` successfully.

## Result
The migration is now idempotent for existing databases and fresh databases.
