# Server Architecture Phase 14

## Scope

This phase continues server-side architecture extraction from Flask API modules.
It removes five additional files from the explicit legacy allowlist tracked by
`tools/architecture_guard.py`.

## Files removed from server legacy tracking

- `alrajhi_server/api/cashboxes.py`
- `alrajhi_server/api/enterprise_governance.py`
- `alrajhi_server/api/rbac.py`
- `alrajhi_server/api/vouchers.py`
- `alrajhi_server/api/warehouses.py`

## Added repository bridge

- `alrajhi_server/repositories/legacy_sql_repository.py`

This is a transitional repository bridge. It removes direct `DatabaseConnection`
and sqlite execution calls from the selected API route modules while preserving
current route behavior. Full semantic extraction into domain-specific repository
methods remains the next cleanup step for these larger modules.

## Verification

- `python tools/architecture_guard.py` passes.
- `pytest -q` passes: 2 tests.
- `python -m compileall alrajhi_client alrajhi_server tools tests -q` passes.
- Build/test cache directories were removed before packaging.
