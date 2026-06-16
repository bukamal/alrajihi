# Phase 143 — Settings Continuation: Backup + Diagnostics Hardening

## Scope
This phase continues the professional Settings module by strengthening the Backup and Diagnostics sections and moving backup preferences from ad-hoc `QSettings` usage into the centralized `SettingsService` infrastructure.

## Implemented

### 1. Centralized Backup Settings
Added `SettingsService.get_backup_settings()` and `SettingsService.save_backup_settings()`.

Stored keys:
- `backup/enabled`
- `backup/frequency`
- `backup/interval_hours`
- `backup/folder`
- `backup/retention_count`
- `backup/create_on_exit`

This keeps backup settings consistent with the rest of the system settings.

### 2. Backup Gateway Expansion
Extended the backup gateway contract with:
- `list_backups(folder, prefix)`
- `cleanup_old_backups(folder, keep_count, prefix)`

Implemented for local SQLite mode and blocked safely in remote mode.

### 3. Backup UI Enhancements
The Backup settings tab now includes:
- Backup frequency: manual / daily / weekly / interval.
- Retention count.
- Create backup on exit flag.
- Last backup status display.
- Refresh backup status button.
- Cleanup old backups button.

Manual backup now refreshes status and applies retention cleanup after creating a backup.

### 4. Diagnostics Page Enhancement
Diagnostics now also reports:
- Whether backup is enabled.
- Backup frequency.
- Backup folder.
- Backup retention count.
- Number of existing backup files.
- Latest backup file and timestamp.

### 5. Validation
Python compilation passed for `alrajhi_client`.

## Files Changed
- `alrajhi_client/core/services/settings_service.py`
- `alrajhi_client/core/services/backup_service.py`
- `alrajhi_client/gateways/backup_gateway.py`
- `alrajhi_client/gateways/local/backup_gateway.py`
- `alrajhi_client/gateways/remote/backup_gateway.py`
- `alrajhi_client/views/widgets/settings_widget.py`

## Practical Result
The Settings module is no longer only a form layer. Backup configuration now has a service/gateway backend, operational status, retention policy, and visibility inside diagnostics.
