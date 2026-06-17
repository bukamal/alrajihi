# Phase 21 — Restaurant UI Integration

## Scope

This phase connects the Phase 20 restaurant foundation to the desktop shell without changing the existing invoice/POS modules.

## Implemented

- Registered a new `restaurant` page in `MainWindow`.
- Added a Restaurant navigation menu and F8 shortcut.
- Added a touch-oriented split restaurant dashboard:
  - table map on the left
  - active order/session panel on the right
- Added `RestaurantPOSWidget` for:
  - loading/opening table sessions
  - adding order lines
  - sending new lines to kitchen/KOT
  - closing the table session
- Localized the new UI in Arabic, German, and English.
- Added Phase 21 structural tests.

## Architectural boundary

UI widgets remain thin wrappers over `RestaurantService`. SQL remains behind gateway/repository layers.

## Verification

- `architecture_guard`: passed
- `pytest`: 8 passed, 1 pre-existing non-fatal warning
- `compileall`: passed
