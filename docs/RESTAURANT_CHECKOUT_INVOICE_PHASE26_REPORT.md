# Phase 26 — Restaurant Checkout to Sales Invoice

## Scope
Converted the restaurant table workflow from a table/order skeleton into a commercial flow that can create a real sales invoice when a table is checked out.

## Added
- `RestaurantGateway.checkout_session(...)` boundary.
- Local checkout implementation that:
  - blocks checkout while new kitchen lines are unsent,
  - creates a posted sale invoice with `RST-xxxxx` reference,
  - writes invoice lines from restaurant order lines,
  - links `restaurant_sessions.invoice_id`,
  - marks served lines,
  - frees the restaurant table.
- Remote gateway endpoint wiring.
- Server endpoint: `POST /api/restaurant/sessions/<session_id>/checkout`.
- Server repository checkout implementation.
- POS button now creates invoice and closes the table instead of merely closing the session.
- Arabic, German, and English translation keys for checkout.

## Validation
- `architecture_guard`: passed.
- `pytest`: 23 passed, one pre-existing non-fatal collection warning.
- `compileall`: passed.
- Cache cleaned after validation.

## Remaining restaurant gaps
- Split bills.
- Partial payments.
- Cashbox/bank selection from POS.
- KDS screen and ticket printing.
- Merge/move tables.
