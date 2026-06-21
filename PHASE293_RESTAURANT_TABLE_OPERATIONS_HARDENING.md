# Phase 293 — Restaurant Table Operations Hardening

## Scope

This phase completes the operational table workflow around the restaurant shell after the order, KDS, payment, printing, recipe-consumption, and visual cleanup phases.

## Implemented

- Added a visible restaurant table operations bar in `RestaurantDashboard`.
- Added reservation, transfer, merge, and selected-line move actions without introducing a separate heavy screen.
- Added reservation and target-table picker dialogs:
  - `RestaurantReservationDialog`
  - `RestaurantTableTargetDialog`
- Preserved the current order, KDS, and table-map flow.
- Exposed table operations through the current shell:
  - reserve free table
  - transfer the current open session to a free/reserved table
  - merge another open table/session into the current one
  - move the selected order line to another table/session
- Added reservation metadata to `list_tables()` so the table map can show reservation context.
- Added reservation seating semantics: opening/transferring into a reserved table marks the active reservation as `seated`.
- Added `restaurant_table_operations` audit-style operation log for local and server repositories.
- Added hardening against duplicate active reservations on the same table.
- Added release-gate coverage and Phase 293 tests.

## Notes

The implementation does not add a full reservation calendar. It provides the operational foundation required by the restaurant floor workflow while keeping the screen compact and touch-friendly.
