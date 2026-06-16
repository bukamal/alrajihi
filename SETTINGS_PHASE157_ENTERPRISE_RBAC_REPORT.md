# Phase 157 — Enterprise RBAC

## Implemented in code

- Added database-backed RBAC tables on client and server migrations:
  - `roles`
  - `permissions`
  - `role_permissions`
  - `user_roles`
  - `user_branch_access`

- Seeded default roles:
  - `admin`
  - `manager`
  - `accountant`
  - `cashier`
  - `viewer`

- Seeded operational permissions:
  - `reports.view`, `reports.export`
  - `invoices.edit`, `invoices.delete`
  - `returns.edit`
  - `branches.view_all`, `branches.manage_all`
  - `approval.submit`, `approval.approve`, `approval.reject`
  - `accounting.view`, `accounting.post`, `accounting.close_period`
  - `settings.manage`, `users.manage`

- Added local client service:
  - `alrajhi_client/core/services/rbac_service.py`

- Updated `PermissionService` to prefer DB-backed RBAC permissions over legacy coarse settings when RBAC tables exist.

- Connected RBAC to:
  - report visibility/export
  - invoice edit/delete permissions
  - return edit permissions
  - branch visibility/manage permissions
  - approval approve/reject permissions
  - accounting posting and period closing permissions

- Added server REST API:
  - `GET /api/rbac/roles`
  - `GET /api/rbac/permissions`
  - `GET /api/rbac/me`
  - `GET/PUT /api/rbac/users/<user_id>/roles`
  - `GET/PUT /api/rbac/roles/<role_name>/permissions`
  - `GET/PUT /api/rbac/users/<user_id>/branches`

- Added `permission_required(permission_key)` decorator foundation on the server.

- Added remote client REST methods for RBAC endpoints.

## Tests performed

- Python compile test:
  - `python3 -m compileall -q alrajhi_client alrajhi_server`
  - Passed.

- Local runtime migration test with PyQt stub:
  - Created a fresh local SQLite database.
  - Verified all RBAC tables exist.
  - Verified default role and permission seed data.
  - Verified accountant role can `accounting.post`.
  - Verified accountant role cannot `approval.approve`.
  - Passed.

## Known limits

- Server runtime API test was not executed in this container because Flask is not installed in the execution environment, but server modules passed `compileall`.
- UI screens for editing roles/permissions are not yet a full dedicated RBAC management console; the backend and service layer are ready.

## Recommended next phase

Phase 158 — Advanced Approval Matrix:

- multi-level approval rules
- amount-based approver matrix
- branch-based approvers
- escalation rules
- approval inbox UI
