# Gateway Phase 14 Report

## Scope
Phase 14 continues the architectural clean-up after Phase 13 by removing direct repository usage from user-facing UI modules and routing user/auth and audit-log screen access through service/gateway boundaries.

## Changes

### 1. User/Auth gateway added
Added:

- `alrajhi_client/gateways/user_gateway.py`
- `alrajhi_client/gateways/local/user_gateway.py`
- `alrajhi_client/gateways/remote/user_gateway.py`
- `alrajhi_client/core/services/user_service.py`

Resulting path:

```text
LoginDialog / UsersWidget / ChangePasswordDialog
→ UserService
→ UserGateway
→ Remote REST API or Local UserRepository
```

### 2. Removed direct `UserRepository` usage from views
Updated:

- `alrajhi_client/views/dialogs/login_dialog.py`
- `alrajhi_client/views/dialogs/change_password_dialog.py`
- `alrajhi_client/views/widgets/users_widget.py`

The login dialog no longer instantiates `DatabaseConnection` directly; remote/local login selection is handled through `UserService`.

### 3. Audit-log widget moved behind AuditService
Updated:

- `alrajhi_client/views/widgets/audit_log_widget.py`
- `alrajhi_client/core/services/audit_service.py`
- `alrajhi_client/gateways/audit_gateway.py`
- `alrajhi_client/gateways/local/audit_gateway.py`
- `alrajhi_client/gateways/remote/audit_gateway.py`

Resulting path:

```text
AuditLogWidget
→ AuditService
→ AuditGateway
→ Remote REST API or Local audit_log table
```

### 4. Architecture guard tightened
Updated:

- `tools/architecture_guard.py`

The guard now blocks direct repository imports from protected UI layers, not only DAO imports.

Tracked legacy direct `DatabaseConnection` exceptions reduced from 4 to 3:

- `alrajhi_client/views/main_window.py`
- `alrajhi_client/views/widgets/settings_widget.py`
- `alrajhi_client/views/widgets/offline_queue_widget.py`

## Validation

```text
python -m compileall -q alrajhi_client tools
python tools/architecture_guard.py
zip -T alrajhi_gateway_phase14.zip
```

All checks passed.

## Remaining legacy work

Next phase should target the remaining 3 direct `DatabaseConnection` exceptions. Recommended order:

1. `offline_queue_widget.py` → `OfflineQueueService`
2. `main_window.py` → app status/service facade
3. `settings_widget.py` → settings/admin database maintenance services
