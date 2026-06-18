# Phase 39 — Invoice Document Tabs

## Scope
This phase extends the Phase 38 tabbed workspace from singleton management pages to document-style invoice tabs.

## Implemented
- Added embedded workspace mode to `InvoiceDialog`.
- Quick sales/purchase invoices now open as independent document tabs instead of modal dialogs.
- Multiple unsaved invoices can be open concurrently.
- Added dirty-state signalling from invoice forms to `TabbedWorkspace`.
- Added saved-state signalling so the tab title updates after invoice save.
- Added workspace command hooks:
  - `workspace_save()`
  - `workspace_print()`
  - `workspace_export()`
  - `workspace_refresh()`
- Added shell shortcuts:
  - `Ctrl+S` saves the current document tab when supported.
  - `Ctrl+P` prints the current document tab when supported.
- Added Arabic, English, and German translations for unsupported workspace commands.

## Architectural Notes
- No SQL or repository access was added to UI shell code.
- Invoice persistence still remains behind `invoice_service`.
- Existing modal invoice behavior remains available because embedded mode is opt-in.

## Verification
- `tools/architecture_guard.py`
- `tools/phase32_invoice_flow_guard.py`
- `tools/phase32_windows_import_guard.py`
- `tools/restaurant_production_readiness_guard.py`
- `pytest`
- `compileall`
