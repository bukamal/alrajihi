# Phase 193 — Manufacturing Workspace Professionalization

This phase upgrades the main manufacturing workspace lists after BOM, production order, lifecycle, unit/API alignment, and printing were already unified.

## Implemented

- Added a stable manufacturing workspace schema for BOM and production-order lists.
- Added translated view presets: compact, planner, warehouse, manager.
- Added BOM search using SmartTableView local filtering.
- Added production-order search, status filter, and warehouse filter.
- Added density controls for compact/comfortable/touch rows.
- Preserved per-user/per-branch/settings-profile layout through SmartTableView/TablePreferences.
- Fixed proxy/source row mapping so context actions open/delete the correct BOM/order after sorting or filtering.
- Removed module-level legacy dialog imports from ManufacturingWidget; legacy dialogs remain fallback only.
- Added Phase 193 guard.

## Principle

The manufacturing workspace now follows the same workspace discipline used by materials, invoices, POS, restaurant, and manufacturing documents: stable columns, translated UI, user-scoped table layout, and document tabs as the primary workflow.
