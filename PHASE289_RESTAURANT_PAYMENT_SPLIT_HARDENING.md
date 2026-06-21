# Phase 289 — Restaurant Payment & Split Bill Hardening

This phase hardens the restaurant payment lane after the order-state and KDS phases.

## Scope

- Added a pure payment/split policy module for deterministic payment caps, split status, billable-line checks, and payment method normalization.
- Hardened local and server restaurant split-bill creation:
  - blocks split creation while unsent kitchen lines still exist;
  - prevents assigning the same order line to more than one active split bill;
  - caps split overpayments to the split subtotal;
  - decorates split bills with `remaining_amount` and `is_paid`.
- Hardened split-bill payments:
  - blocks zero/negative payments;
  - caps overpayment to the remaining split amount;
  - records applied amount and session balance.
- Hardened mixed payments:
  - ordinary partial payments and split payments both update the same session balance;
  - checkout remains blocked until the restaurant session is fully paid.
- Added an operational UI action for creating and optionally paying a split bill from the selected order line.

## Compatibility note

The legacy administrative `close_session()` API remains backward compatible for old tests/plugins. The actual operation button uses `checkout_session()`, which is fully payment-gated.

## Verification

- `tests/test_phase289_restaurant_payment_split_hardening.py`
- Restaurant regression tests
- Release packaging/readiness guards
