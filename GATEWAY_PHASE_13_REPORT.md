# Gateway Phase 13 Report

## Scope

Phase 13 removes direct `DatabaseConnection` usage from infrastructure-facing core services:

- `core/services/audit_service.py`
- `core/services/backup_service.py`

## Added gateways

- `gateways/audit_gateway.py`
- `gateways/local/audit_gateway.py`
- `gateways/remote/audit_gateway.py`
- `gateways/backup_gateway.py`
- `gateways/local/backup_gateway.py`
- `gateways/remote/backup_gateway.py`

## Resulting paths

```text
AuditService
→ AuditGateway
→ Local audit_log writer or Remote no-op
```

```text
BackupService
→ BackupGateway
→ Local SQLite backup/restore adapter or Remote blocked adapter
```

## Architectural impact

- Core services no longer import `DatabaseConnection` for audit or backup.
- Direct database access remains isolated inside `gateways/local/*` and gateway factories.
- Architecture guard allow-list reduced from 6 legacy files to 4 legacy UI files.

## Verification

- `python tools/architecture_guard.py`
- `python -m compileall alrajhi_client alrajhi_server tools`
- ZIP integrity test
