# Server Architecture Phase 16

## Scope
Phase 16 continues the server-side extraction that started after the client-side gateway cleanup. It reduces dependency on the transitional `LegacySqlRepository` by moving selected Flask API persistence logic into purpose-specific repositories.

## Refactored API modules
- `alrajhi_server/api/rbac.py`
- `alrajhi_server/api/enterprise_governance.py`
- `alrajhi_server/api/vouchers.py`

## New repositories
- `alrajhi_server/repositories/rbac_repository.py`
- `alrajhi_server/repositories/governance_repository.py`
- `alrajhi_server/repositories/voucher_repository.py`

## Important behavioral note
`enterprise_governance.validate_backup_restore` previously used `sqlite3.Connection.query`, which is not a valid sqlite3 API method. It now uses `execute` for `PRAGMA integrity_check` and table counting.

## Legacy bridge status
API files still using `LegacySqlRepository` after this phase:
- `cashboxes.py`
- `invoices.py`
- `items.py`
- `manufacturing.py`
- `reports.py`
- `returns.py`
- `warehouses.py`

## Verification
- `python tools/architecture_guard.py`: passed
- `pytest -q`: passed, 2 tests, one pre-existing non-fatal collection warning
- `python -m compileall -q alrajhi_client alrajhi_server tools tests`: passed
- Build/test cache directories removed before packaging
