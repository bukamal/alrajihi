# Structure remediation notes

Applied structural changes:

1. Moved Settings diagnostics database access out of `alrajhi_client/views/widgets/settings_widget.py`.
   - UI now calls `system_service.local_diagnostics_snapshot()` and `system_service.integrity_checks()`.
   - Raw SQLite calls are isolated behind `alrajhi_client/gateways/local/system_gateway.py`.

2. Moved `SystemService.integrity_checks()` raw SQLite access behind `SystemGateway`.
   - `system_service.py` no longer imports `DatabaseConnection` directly.

3. Reduced tracked architecture debt in `tools/architecture_guard.py`.
   - Legacy DatabaseConnection exceptions: 12 -> 10 files.
   - Legacy direct SQL exceptions: 12 -> 10 files.

4. Project-root cleanup.
   - Root phase/audit/report markdown files moved to `docs/archived_reports/`.
   - `test_reports/` and localization audit output moved to `docs/archived_reports/`.
   - Runtime/cache artifacts removed: `__pycache__/`, `.pytest_cache/`.
   - Added `.gitignore` baseline.

5. Test collection stabilized.
   - Added `pytest.ini` to restrict pytest collection to `tests/` and avoid executing operational scripts under `tools/` as tests.

Validation run:

- `python tools/architecture_guard.py` -> passed.
- `python -m pytest -q` -> 2 passed, 1 existing collection warning.
- `python -m compileall -q alrajhi_client alrajhi_server tools tests` -> passed.

Remaining structural debt:

- 10 protected files still have tracked direct local DB/SQL access.
- Server API routes still need a service/repository boundary before SQL can be considered cleanly isolated.
- Remote mode still needs endpoint parity for some gateway methods.

## Phase 2 structural remediation

Implemented additional safe boundary reductions:

- Moved `SystemHealthService` database work behind `SystemGateway.run_health_checks()`.
- Converted `SystemHealthService.ensure_schema()` to a compatibility no-op; schema ownership now belongs to the gateway layer.
- Moved permission/security event persistence from `PermissionService` behind `SystemGateway` methods:
  - `log_security_event()`
  - `security_events()`
  - `denied_security_events_count()`
- Updated `LocalSystemGateway` to own the local SQLite implementation for health checks and security events.
- Reduced architecture debt allow-list from 10 to 8 files.

Validation:

- `python tools/architecture_guard.py` passes.
- `python -m pytest -q` passes: 2 passed, 1 collection warning.
- `python -m compileall -q ...` passes for modified modules.

Remaining tracked direct local SQL services:

- `accounting_service.py`
- `advanced_approval_service.py`
- `approval_service.py`
- `production_validation_service.py`
- `rbac_service.py`
- `reporting_service.py`
- `settings_service.py`
- `workflow_policy_service.py`

## Phase 3 structural remediation

- Reduced tracked architecture exceptions from 8 to 6.
- Moved `ProductionValidationService` database writes and validation SQL behind `SystemGateway`.
- Added gateway-backed backup/restore validation and stress-smoke persistence methods.
- Moved `ApprovalService` approval-request persistence behind a dedicated `ApprovalGateway`.
- Added `gateways/approval_gateway.py` and `gateways/local/approval_gateway.py` to keep approval SQL outside protected service layers.
- Verification performed:
  - `python tools/architecture_guard.py`
  - `pytest -q`
  - `python -m compileall -q alrajhi_client alrajhi_server tools tests`

Remaining tracked legacy service exceptions: 6.

## Phase 5 structural remediation

- Moved RBAC persistence behind a new `RBACGateway` boundary.
- Added `gateways/rbac_gateway.py` contract/factory with safe remote fallback.
- Added `gateways/local/rbac_gateway.py` for local SQLite-backed roles, permissions, role assignment, and branch access.
- Refactored `core/services/rbac_service.py` so it no longer imports `DatabaseConnection` and no longer executes SQL directly.
- Removed `rbac_service.py` from the architecture-guard legacy allowlist.

Validation:

- `python tools/architecture_guard.py` passed with 4 tracked legacy DB/SQL exceptions.
- `pytest -q` passed: 2 tests.
- `python -m compileall -q alrajhi_client alrajhi_server tools tests` passed.

## Phase 6 structural remediation

- Added `WorkflowGateway` and `LocalWorkflowGateway`.
- Moved invoice workflow schema, transition persistence and diagnostics SQL out of `core/services/workflow_policy_service.py`.
- Reduced architecture guard legacy direct database exceptions from 4 files to 3 files.
- Verification:
  - `python tools/architecture_guard.py` passed.
  - `python -m pytest -q` passed: 2 tests.
  - `python -m compileall -q alrajhi_client alrajhi_server tests tools` passed.

Known note:
- Repository-root `compileall` still exposes a pre-existing syntax error in the historical helper script `apply_phase152_153.py`; package-level compile verification passed for runtime code.

## Phase 7 structural remediation

- Moved SettingsService profile/audit/export persistence access behind the SettingsGateway boundary.
- Added local SettingsGateway operations for settings audit rows, settings export/import, and settings profiles.
- Removed `settings_service.py` from the architecture guard legacy SQL/DatabaseConnection allow-list.
- Architecture debt reduced from 3 tracked service-layer DatabaseConnection/SQL exceptions to 2.

Verification:

- `python tools/architecture_guard.py` passes with 2 tracked legacy exceptions.
- `pytest -q` passes: 2 tests.
- `python -m compileall -q alrajhi_client alrajhi_server tools` passes.

## Phase 8
- Moved `AccountingService` direct SQLite/DatabaseConnection implementation behind `gateways/local/accounting_gateway.py`.
- Added `gateways/accounting_gateway.py` factory.
- Converted `core/services/accounting_service.py` into a facade delegating to the accounting gateway.
- Reduced tracked architecture exceptions from 2 to 1; only `reporting_service.py` remains as legacy direct SQL access.
- Verification: architecture guard passed, pytest passed, compileall passed.

## Phase 9 - Reporting service boundary completion

- Removed the final architecture-guard allowlist entry for `alrajhi_client/core/services/reporting_service.py`.
- Moved direct reporting SQL and `DatabaseConnection` access from `ReportingService` into `LocalReportingGateway`.
- Extended `ReportingGateway` and `RemoteReportingGateway` with safe report-method contracts/stubs for advanced reports.
- `ReportingService` now delegates advanced reports through the reporting gateway while retaining branch-scope resolution at service level.

Validation:
- `python tools/architecture_guard.py` passes with 0 tracked legacy database exceptions and 0 tracked SQL exceptions.
- `pytest -q` passes: 2 passed.
- `python -m compileall -q alrajhi_client alrajhi_server tools` passes.
