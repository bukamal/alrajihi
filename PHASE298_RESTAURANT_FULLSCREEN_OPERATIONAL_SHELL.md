# Phase 298 — Restaurant Fullscreen Operational Shell & Money Closure

## Scope
This phase replaces the cramped three-pane restaurant layout with stacked fullscreen operational modes.
The restaurant no longer attempts to show current order, KDS, table map, and analytics as simultaneous major panes on laptop/operator screens.

## Implemented

- Added `restaurantFullscreenModeStack` as the primary restaurant workspace.
- Converted restaurant modes into exclusive pages:
  - Current order page: table map + current order, with current order as the dominant pane.
  - Kitchen page: KDS as the dominant pane, with optional table context only when there is enough width.
  - Tables page: full table map for search/reservation/transfer/merge workflows.
  - Analytics page: only when enabled by settings.
- Preserved legacy object names such as `restaurantOperationSplitter` and `restaurantSideModeStack` for compatibility, while the active shell no longer lays KDS/order/tables as three cramped panes.
- Changed restaurant POS to use compact decisive money summaries on non-wide operator screens.
- Formatted restaurant menu item card prices through the same display-money path as order lines and totals.
- Added `restaurant.mode.tables` translations in Arabic, English, and German.
- Added QSS for fullscreen restaurant workspace pages and compact action rendering.

## Money closure
Restaurant visible amounts now go through the display-money formatter in:

- Menu item cards.
- Order summary cards.
- Order line grid.
- Table map totals.
- Payment/split/status messages.

This prevents raw base currency values such as `1.428571428...` appearing in the restaurant menu/cards.

## Non-goals
This phase does not remove the main application topbar.  It restructures the restaurant workspace itself so it is usable inside the existing shell.  Full application kiosk mode can be added later as a separate controlled feature.
