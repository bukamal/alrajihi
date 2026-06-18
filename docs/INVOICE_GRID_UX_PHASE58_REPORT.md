# Phase 58 — Invoice Grid UX + Enterprise Smart Tables

## Scope
- Reworked sale/purchase invoice creation into a document-like workspace layout.
- Made the invoice lines table the dominant extended area of the screen.
- Moved primary actions to a bottom action bar.
- Added a splitter-based body so the grid/summary areas adapt to window resize.
- Strengthened `SmartTableView` with responsive column fitting, draggable column order, column hide/show, and persisted layout state.

## Preserved boundaries
- No SQL/data access was added to UI.
- Unified printing remains the print route.
- Existing invoice services, unit-aware lines, and document tab state remain intact.

## Guard
`tools/invoice_grid_ux_guard.py`
