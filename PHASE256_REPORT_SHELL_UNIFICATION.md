# PHASE256_REPORT_SHELL_UNIFICATION

## Scope
Unify the reports workspace as a governed Report Shell without forcing it into an editable document tab.

## Changes
- Added `features/reports/report_shell_contract.py` with per-report descriptors.
- Bound `ReportsWidget` to the global `reports` DocumentDescriptor and `DocumentPermissionBinder`.
- Attached stable report metadata to every report table: `report_key`, `report_api_resource`, `report_network_mode`, and currency policy.
- Added `report_operation_policy.OP_PRINT` and `reports/operations/allow_print` so printing is not conflated with export.
- Report print output now includes Report Shell metadata in the HTML summary and still uses Browser HTML.
- Added `tools/report_shell_contract_audit.py` and static tests.

## Network note
Core financial/customer/supplier reports declare `remote_available`. Composite operational reports declare `mixed` or `local_only` until endpoint parity is completed. This is deliberate: the shell now tells the truth instead of claiming full API coverage silently.
