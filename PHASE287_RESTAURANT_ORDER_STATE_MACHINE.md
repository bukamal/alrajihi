# Phase 287 — Restaurant Order State Machine

This phase makes restaurant table/session state deterministic instead of leaving
it as manual UI decoration.

Implemented:
- `features.restaurant.restaurant_order_state` derives order/table states from
  order-line kitchen statuses and payment balance.
- Local restaurant gateway syncs session/table state after line add, kitchen
  send, kitchen status updates, payments, and checkout.
- Table-map payloads now expose `active_order_state`, `active_kitchen_state`,
  `active_total`, `active_remaining`, `payment_pending`, and `ui_status`.
- Restaurant POS now shows a state badge and enables actions according to the
  session state: send kitchen only for new lines, payment only when payable,
  checkout only when fully paid.
- Added AR/DE/EN labels and QSS for restaurant order states.

State chain:
`editing -> kitchen -> ready -> payment_due -> paid -> closed`.
