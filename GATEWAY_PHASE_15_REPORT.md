# Gateway Phase 15 Report

## Scope
Phase 15 removes the remaining direct `DatabaseConnection`/offline queue access from protected UI layers.

## Changes
- Added runtime diagnostics boundary:
  - `alrajhi_client/gateways/system_gateway.py`
  - `alrajhi_client/gateways/local/system_gateway.py`
  - `alrajhi_client/core/services/system_service.py`
- Added offline queue boundary:
  - `alrajhi_client/gateways/offline_queue_gateway.py`
  - `alrajhi_client/gateways/local/offline_queue_gateway.py`
  - `alrajhi_client/core/services/offline_queue_service.py`
- Updated `MainWindow` to use `system_service` and `offline_queue_service` instead of `DatabaseConnection`/`offline_queue` imports.
- Updated `OfflineQueueWidget` to use `offline_queue_service`.
- Updated `SettingsWidget` to use `system_service` for diagnostics/request log and `backup_service.reset_database()` for reset.
- Extended `BackupGateway`/`BackupService` with `reset_database()` so reset logic is no longer in the UI.
- Tightened `tools/architecture_guard.py` allow-list to zero legacy `DatabaseConnection` exceptions.

## Validation
- `python tools/architecture_guard.py` passes.
- Legacy DatabaseConnection exceptions: `0`.
- `python -m compileall -q alrajhi_client alrajhi_server tools` passes.
- ZIP integrity test passes.

## Remaining architectural note
Direct `DatabaseConnection` access still exists inside gateway/factory/local adapter boundaries by design. The protected layers (`views` and `core/services`) are now clean under the architecture guard.
