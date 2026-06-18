# Phase 208 — Migration Permission Insert Hotfix

## Problem

Application startup failed during local database initialization with:

```text
sqlite3.OperationalError: 18 values for 4 columns
```

The failure was caused by a malformed `INSERT OR IGNORE INTO permissions(key,module,action,description)` statement in both client and server migrations. The statement declared four columns but attempted to insert `inventory.print` plus multiple finance permission keys in the same tuple.

## Fix

The malformed row was replaced with a correct single permission row:

```sql
INSERT OR IGNORE INTO permissions(key,module,action,description)
VALUES ('inventory.print','inventory','print','Print inventory and warehouse documents');
```

Finance, cashbox, bank, and voucher permissions are now inserted as separate four-value rows:

```text
finance.use
finance.cashbox.create
finance.cashbox.edit
finance.cashbox.archive
finance.bank.create
finance.bank.edit
finance.bank.archive
finance.movements.view
finance.shifts.view
finance.voucher.view
finance.voucher.create
finance.voucher.edit
finance.voucher.delete
finance.voucher.print
```

Role grants were also added explicitly for manager/admin, accountant, and cashier scopes so these permissions are not merely present in RBAC defaults but also seeded into `role_permissions`.

## Files touched

```text
alrajhi_client/database/migrations.py
alrajhi_server/database/migrations.py
tools/phase208_migration_permission_insert_guard.py
```

## Guard

Added:

```text
tools/phase208_migration_permission_insert_guard.py
```

The guard checks that:

- every `permissions(key,module,action,description)` tuple has exactly four values;
- `inventory.print` is not merged with finance permissions;
- all finance permission keys are inserted as separate rows;
- both client and server migrations are covered.

## Validation

Executed successfully:

```text
python -m compileall -q alrajhi_client alrajhi_server
python tools/phase198_startup_circular_import_guard.py
python tools/phase199_startup_import_boundary_guard.py
python tools/phase208_migration_permission_insert_guard.py
```
