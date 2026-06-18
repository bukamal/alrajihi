# Phase 206 — User Document Governance

## Goal
Move user create/edit into the tabbed workspace and protect user-management operations through a unified settings/RBAC policy.

## Changes
- Added `core/services/user_operation_policy.py`.
- Added `features/users/documents/user_document_tab.py`.
- Added `features/users/__init__.py` export.
- Added `settings_service.get_user_settings()`.
- Added `PermissionService.ACTION_USERS_MANAGE` mapped to `users.manage`.
- Guarded `UserService` methods through `user_operation_policy`:
  - `list_users`
  - `get_user`
  - `create_user`
  - `update_user`
  - `change_password`
  - `delete_user`
- Updated `UsersWidget` to open `UserDocumentTab` through `MainWindow.open_user_document()`.
- Made selected-row handling proxy/source safe using `current_source_row()` / `mapToSource` fallback.
- Added i18n keys for Arabic, English, and German.
- Added `tools/phase206_user_document_governance_guard.py`.

## Compatibility
The legacy `UserDialog` remains available as a fallback if the main window cannot open workspace tabs.

## Checks
- `python tools/phase198_startup_circular_import_guard.py`
- `python tools/phase199_startup_import_boundary_guard.py`
- `python tools/phase206_user_document_governance_guard.py`
- `python -m compileall -q alrajhi_client alrajhi_server`
