# Phase 430 — POS Barcode Table First Layout

## Purpose

Phase 430 removes the POS material card strip that was introduced by Phase 428. The POS screen is now barcode/table-first: the cashier scans or searches from the barcode field, while the cart table owns the main vertical workspace.

Restaurant and Cafe keep the three-column material card grid because those workflows are touch/menu driven.

## Scope

- POS no longer imports `OperationalItemCardGrid`.
- POS no longer creates `posOperationalItemCardGrid`.
- POS no longer loads catalog items into cards above the cart table.
- POS keeps the barcode/search field, quantity field, camera scan, cart grid, and payment shell.
- Restaurant/Cafe item-card grids remain unchanged.
- Enter navigation, payment, printing, inventory, and checkout logic are not changed.

## Rationale

POS is primarily a cashier and barcode workflow. A material card surface above the cart table competes with scan speed and table visibility. Restaurant/Cafe need card-based selection because the operator chooses from menu categories and touch surfaces.

## Acceptance Criteria

- `views/widgets/pos_widget.py` contains no POS material-card grid.
- `POSLineGrid` remains directly below the scan row.
- `set_global_filter()` only updates the barcode/search input and focus.
- Shared `OperationalItemCardGrid` remains available for Restaurant/Cafe.
- Phase 428 guard is updated to reflect the new boundary: card grid is shared for Restaurant/Cafe, not POS.
