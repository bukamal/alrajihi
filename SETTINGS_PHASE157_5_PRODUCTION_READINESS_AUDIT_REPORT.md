# Phase 157.5 — Production Readiness Audit & Migration Hardening

## Scope
This audit was run on `alrajhi_gateway_phase157_enterprise_rbac_hotfix_due_date(1).zip`.

## What was tested

### Static validation
- Python compile check for `alrajhi_client` and `alrajhi_server`.
- Result: PASSED.

### Fresh client database
- Created a new local client database with `ensure_db()`.
- Re-ran `ensure_db()` on the same database to verify idempotency.
- Result: PASSED.

### Fresh server database
- Created a new server database using `ALRAJHI_SERVER_DB_PATH`.
- Re-ran `ensure_db()` on the same database to verify idempotency.
- Result: PASSED.

### Legacy client database upgrade
A deliberately old/minimal database was created with:
- legacy `users`
- legacy `customers`
- legacy `suppliers`
- legacy `invoices` with existing `due_date`
- legacy `items`
- legacy `warehouses`
- legacy `expenses`

Initial result before repair:
- FAILED due to missing old-schema columns such as `users.full_name` and `items.quantity`.

Repair applied:
- Hardened `schema_manager.py` for both client and server.
- Added missing legacy upgrade columns:
  - `users.full_name`
  - `users.created_at`
  - `users.last_login`
  - `customers.phone/address/balance`
  - `suppliers.phone/address/balance`
  - `items.purchase_price/selling_price/quantity/unit`
  - `warehouses.user_id`
  - `branches.user_id`
  - `expenses.user_id`
  - `invoices.due_date`
- Moved/common-schema normalization earlier before default-data and index creation.
- Hardened index creation to skip unavailable legacy columns/tables instead of stopping startup.

Final result:
- PASSED.

### Legacy server database upgrade
- Same old/minimal database pattern tested against server migrations.
- Result after repair: PASSED.

### End-to-end operational test
Executed a core ERP chain on a fresh client database:

1. Initialize database.
2. Create admin session.
3. Set sales approval threshold.
4. Create customer.
5. Create sales invoice.
6. Create approval request.
7. Submit invoice.
8. Approve invoice.
9. Post invoice to accounting.
10. Generate journal entry.
11. Verify trial balance is balanced.
12. Verify ledger has journal lines.
13. Verify income statement net income.
14. Verify balance sheet is balanced.
15. Close accounting period.

Result:
- PASSED.

## Confirmed tables
The following required governance/accounting/security tables were confirmed:
- `roles`
- `permissions`
- `role_permissions`
- `user_roles`
- `user_branch_access`
- `accounts`
- `journal_entries`
- `journal_lines`
- `accounting_periods`
- `approval_requests`
- `workflow_events`

## Remaining limitations
This audit confirms startup, migrations, RBAC foundation, approval foundation, accounting posting, and financial closing in a controlled runtime scenario.

Still not fully covered:
- Real PyQt GUI click testing.
- Multi-user concurrent approval.
- Network API live server test with HTTP client.
- Large production dataset performance test.
- Full manufacturing-to-accounting cost posting.
- Browser/desktop UI automation.

## Result
The project is significantly more production-ready after this hardening pass. The previous recurring migration-class errors (`workflow_status`, `due_date`, missing old columns) were addressed by idempotent schema upgrades and safer index creation.
