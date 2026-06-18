# Phase 54 — UI Consistency Guard

## Objective
Lock the project into the new document-based workspace direction and prevent silent regression to large modal CRUD windows.

## Added
- `tools/ui_consistency_guard.py`
- Explicit allowlist for legacy heavy UI files that remain as migration debt.
- Required wiring checks for:
  - `TabbedWorkspace`
  - `UnifiedActionBar`
  - `BaseDocumentTab`
  - `DialogDocumentTab`
  - `SmartTableView`
- Delegation checks for major CRUD screens so add/edit flows route through workspace/document tabs.

## Policy
Large business operations must be workspace document tabs. Dialogs remain acceptable only for small utility flows such as quick open, print selection, confirmation, or temporary explicitly documented legacy bridges.

## Current explicit migration debt
- `invoice_dialog.py`
- `returns_widget.py`
- `settings_widget.py`
- `reports_widget.py`

These files should be reduced in Phase 55+ rather than used as patterns for new work.
