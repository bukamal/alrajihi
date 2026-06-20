# Phase 283 — Restaurant Operation Shell UX

## Goal

Professionalize the restaurant screen so it behaves as an operation shell, not a mixed dashboard. The default screen now prioritizes the live table/order workflow and moves kitchen/analytics into explicit modes.

## Changes

- `RestaurantDashboard` now opens in a two-pane layout by default: table map + current order/menu.
- Kitchen display is available through an explicit mode button instead of permanently occupying screen space.
- Restaurant analytics are hidden from the operational screen by default and are controlled by `restaurant/ui/show_analytics_panel`.
- Added settings-backed UI controls:
  - `restaurant/ui/show_kitchen_panel`
  - `restaurant/ui/show_analytics_panel`
  - `restaurant/ui/table_card_density`
- `RestaurantPOSWidget` prioritizes the current order grid and bottom operation actions; menu search/cards are lower priority.
- Table cards now expose richer statuses: free, occupied, waiting for kitchen, ready, payment, reserved.
- Table cards may show order total and elapsed minutes when the service provides these fields.
- Added translations for the new operation-shell labels and settings.

## Scope

This phase does not remove kitchen/analytics features. It changes their visibility and placement to reduce clutter during live service.
