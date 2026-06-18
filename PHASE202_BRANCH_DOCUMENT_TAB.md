# Phase 202 — Branch Document Tab

## Summary

Phase 202 migrates branch create/edit from the legacy `BranchDialog` path to a workspace document tab.

## Key changes

- Added `features/branches/documents/branch_document_tab.py`.
- Added `BranchDocumentTab -> BaseDocumentTab`.
- Added `MainWindow.open_branch_document()`.
- Updated `BranchesWidget.add_branch()` and `BranchesWidget.edit_branch()` to prefer the tabbed document path with legacy `BranchDialog` fallback.
- Added `core/services/branch_operation_policy.py`.
- Added `settings_service.get_branch_settings()`.
- Routed branch create/edit/archive/default operations through `branch_operation_policy` and `BranchService`.
- Fixed selected-row handling in `BranchesWidget` to use `SmartTableView.current_source_row()` when filters/sorting are active.
- Replaced the hard-coded default branch button label with i18n.

## Guard

`tools/phase202_branch_document_tab_guard.py`
