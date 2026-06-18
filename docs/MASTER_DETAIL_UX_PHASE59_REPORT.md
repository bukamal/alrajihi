# Phase 59 — Master-Detail UX Rollout

## Scope

Phase 59 extends the Phase 58 invoice/grid work to the high-frequency management screens.
It focuses on resize behavior, preview panels, and keeping SmartTableView as the unified table control.

## Implemented

- Added `ui/components/responsive_master_detail.py`.
- Added reusable `ResponsiveMasterDetail` based on `QSplitter`.
- Added reusable `DetailPlaceholder` for safe read-only previews.
- Converted Customers screen to master/detail layout.
- Converted Suppliers screen to master/detail layout.
- Converted Item editor body to a horizontal `QSplitter` so basic/pricing/units panels resize cleanly.
- Added `tools/master_detail_ux_guard.py`.
- Added Phase 59 tests.

## Design rule

Large ERP management pages should not remain fixed vertical stacks. They should use:

- `SmartTableView` for the master list.
- `ResponsiveMasterDetail`/`QSplitter` for available screen width.
- Document Tabs for editing.
- Dialogs only for short confirmations or quick choices.

## Printing and data boundaries

No printing path was changed. The existing unified printing remains intact.
No data access was added to UI components; preview panels consume already loaded row data only.
