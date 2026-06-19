# Phase 212 — Full Runtime / CI Stabilization

This phase is a stabilization phase. It does not add a new UI module. It hardens startup/runtime contracts after the recent regressions around circular imports, migrations, DAO lazy exports, and report contract checks.

## Changes

- Added `is_remote() -> bool` to remaining local gateway classes that did not implement the shared gateway contract:
  - `LocalAccountingGateway`
  - `LocalApprovalGateway`
  - `LocalIndustryGateway`
  - `LocalRBACGateway`
  - `LocalRestaurantGateway`
  - `LocalWorkflowGateway`
- Added `tools/phase212_runtime_stabilization_guard.py`.
- The new guard runs headlessly with a PyQt5 shim when PyQt5 is unavailable.
- The guard validates:
  - local database bootstrap on a fresh temporary database,
  - core service imports,
  - gateway factory instantiation,
  - `is_remote()` existence and boolean return value on all gateway objects,
  - `database.expense_dao` exports a DAO object with `get_all()` rather than the submodule.

## Validation

Run:

```bash
python tools/phase212_runtime_stabilization_guard.py
python tools/advanced_runtime_test.py
python tools/reports_contract_check.py
python tools/phase198_startup_circular_import_guard.py
python tools/phase199_startup_import_boundary_guard.py
python tools/phase208_migration_permission_insert_guard.py
python tools/phase210_expense_dao_export_hotfix_guard.py
python -m compileall -q alrajhi_client alrajhi_server
```

Expected result: all checks pass.
