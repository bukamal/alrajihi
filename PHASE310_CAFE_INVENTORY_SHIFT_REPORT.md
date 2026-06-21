# Phase 310 — Cafe Inventory & Shift Report

This phase completes the first cafe vertical slice as a cafe-specific operational report built on the restaurant engine.

## Scope

- Adds `cafe_shift_report` to local, remote, service, abstract gateway, and server HTTP route.
- Filters all report data to `order_type = cafe_quick_order`.
- Adds cafe order totals, payments, open/unpaid order blockers, active Barista ticket blockers, and queued print blockers.
- Adds top drinks and top modifiers/add-ons.
- Adds recipe inventory consumption aggregation for cafe orders.
- Adds low-stock alerts for consumed cafe components using existing item `reorder_level`.
- Updates the analytics panel so cafe report mode calls the cafe report rather than the generic restaurant report.

## Non-goals

- No separate cafe accounting engine.
- No separate cafe printing engine.
- No currency calculations in the UI.
