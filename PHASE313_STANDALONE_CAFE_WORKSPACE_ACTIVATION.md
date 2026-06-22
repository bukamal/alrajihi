# Phase 313 — Standalone Cafe Workspace Activation

## Goal

Expose the cafe as a standalone top-level workspace controlled by `cafe/enabled`, while keeping the audited restaurant engine for quick orders, payments, browser-HTML printing, inventory/recipe consumption, currency display, and shift reporting.

## Scope

- Added a standalone `cafe` page to main navigation and quick-open context.
- Added `CafeWorkspaceWidget`, a visual cafe workspace backed by `RestaurantDashboard(workspace_context="cafe")`.
- The standalone cafe workspace hides table-service modes and routes operators to quick order, Barista preparation, and cafe shift report.
- Added `cafe/enabled` to module visibility, settings contracts, and the visible settings screen.
- Added a `CafeSettingsTab` for cafe activation, quick-order behavior, preparation route, and cafe printer/paper preferences.
- Added canonical cafe permission keys while aliasing them to the existing restaurant operation permissions so no parallel authorization system is introduced.
- Added a pure Python activation contract and release gate test to prevent creation of a separate cafe engine.

## Non-goals

- No `cafe_gateway.py`, `cafe_repository.py`, `cafe_payment_service.py`, or `cafe_printing_service.py` was added.
- Cafe remains a UI/module separation, not a duplicated business engine.

## Runtime contract

`cafe/enabled = false` hides the cafe page and settings section from navigation. `cafe/enabled = true` exposes a standalone cafe workspace. Internally, orders still use `cafe_quick_order` through the restaurant gateway/service/API path.
