# Phase 10 — Server Architecture Remediation

## Scope

This phase starts the server-side refactor. It does not attempt to rewrite all Flask routes in one risky pass. Instead, it introduces a server repository layer and moves low-risk CRUD/data-access routes out of direct SQL first.

## Implemented

Added `alrajhi_server/repositories/` as the server data-access layer.

Moved direct database access out of these API modules:

- `alrajhi_server/api/customers.py`
- `alrajhi_server/api/suppliers.py`
- `alrajhi_server/api/expenses.py`
- `alrajhi_server/api/settings.py`
- `alrajhi_server/api/audit_log.py`

New repositories:

- `PartyRepository` for customer/supplier CRUD
- `ExpenseRepository`
- `SettingsRepository`
- `AuditLogRepository`

Extended `tools/architecture_guard.py` so it now scans `alrajhi_server/api` in addition to protected client layers. Remaining direct SQL routes are tracked in an explicit server legacy allowlist.

## Current server legacy allowlist

The following API modules still contain direct DB/SQL access and must be migrated in later phases:

- `audit_utils.py`
- `auth.py`
- `branches.py`
- `cashboxes.py`
- `categories.py`
- `debug.py`
- `enterprise_governance.py`
- `invoices.py`
- `items.py`
- `manufacturing.py`
- `rbac.py`
- `reports.py`
- `returns.py`
- `users.py`
- `vouchers.py`
- `warehouses.py`

## Verification

- `python tools/architecture_guard.py` passed.
- `pytest -q` passed: 2 tests.
- `python -m compileall -q alrajhi_client alrajhi_server tools tests` passed.

## Recommendation for Phase 11

Continue with another low-to-medium risk batch before touching high-complexity domains. Suggested next targets:

1. `categories.py`
2. `branches.py`
3. `users.py` only after checking auth/RBAC coupling

Avoid starting with `invoices.py`, `manufacturing.py`, `returns.py`, or `items.py`; those routes contain business transactions and inventory/accounting side effects.
