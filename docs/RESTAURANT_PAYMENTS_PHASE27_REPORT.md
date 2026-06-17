# Phase 27 — Restaurant Split Payments

## Scope
Implemented a restaurant payment layer after table ordering and before final checkout.

## Added
- `restaurant_payments` table for posted restaurant session payments.
- `session_balance(session_id)` boundary method.
- `record_payment(session_id, amount, payment_method, notes)` boundary method.
- Client gateway/service/remote wiring for payments and balances.
- Server endpoints:
  - `GET /api/restaurant/sessions/<session_id>/balance`
  - `POST /api/restaurant/sessions/<session_id>/payments`
- Touch payment dialog in the restaurant POS widget.
- Split-payment behavior: multiple payments can be posted before checkout.
- Checkout guard: a table cannot be closed until the restaurant session is fully paid.
- Automatic full payment remains backward-compatible when checkout is called with no prior payments and no explicit `paid_amount`.

## Validation
- `architecture_guard`: passed.
- `pytest`: 25 passed, 1 pre-existing non-fatal warning.
- `compileall`: passed.

## Notes
This phase does not yet post restaurant payments into cashbox/bank ledger movements. It records restaurant-session payments and links them to the generated invoice. The next accounting-hardening step should bridge posted restaurant payments into the existing cashbox/bank accounting workflows.
