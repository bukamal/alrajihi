# Phase 64 — Full Table Standardization

## Goal
Standardize all project tables under two explicit UI primitives:

- `SmartTableView` for read-only/model-backed ERP tables.
- `EditableSmartGrid` for editable line-entry and matrix tables.

This phase removes direct table construction from business screens and keeps column personalization available across the project.

## Implemented

### New editable grid primitive
Added:

- `alrajhi_client/ui/editable_smart_grid.py`

It provides:

- column show/hide
- movable columns
- persisted header layout
- responsive column fitting
- row density profiles
- copy selection
- saved view presets
- guarded prevention of hiding all columns

### Converted editable tables
Converted direct `QTableWidget` usage to `EditableSmartGrid` in:

- POS lines
- return lines
- item unit conversions
- legacy item dialog unit conversions
- settings exchange rates
- settings profiles
- settings audit
- settings security events
- offline queue
- monitoring overview

### Converted legacy model-backed dialogs
Converted direct `CustomTableView` usage to `SmartTableView` in:

- batch print item selection
- production order required materials
- production details consumption/output/residuals

### Guard
Added:

- `tools/full_table_standardization_guard.py`

The guard blocks:

- direct `QTableWidget(...)` construction outside the standard editable wrapper and documented legacy scanner helpers
- direct `CustomTableView(...)` construction outside `SmartTableView`
- missing required table identities for standardized screens

## Verification

Passed:

- `python tools/architecture_guard.py`
- `python tools/release_hardening_guard.py`
- `python tools/unified_printing_guard.py`
- `python tools/enterprise_table_ux_guard.py`
- `python tools/enterprise_filter_ux_guard.py`
- `python tools/invoice_grid_ux_guard.py`
- `python tools/invoice_table_input_ux_guard.py`
- `python tools/phase63_invoice_quick_entry_guard.py`
- `python tools/full_table_standardization_guard.py`
- `pytest -q` → 101 passed, 1 existing warning
- `python -m compileall -q alrajhi_client alrajhi_server tools`

## Notes

Styling and scanner references to `QTableWidget` remain where they are not table implementations:

- theme/QSS selectors
- modern UI styling introspection
- `DialogDocumentTab` legacy dirty-state scanner
- `EditableSmartGrid` itself

No new data access was introduced in UI code.
