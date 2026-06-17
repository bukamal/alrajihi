# Restaurant Phase 23 - Order Lifecycle Hardening

## Scope
This phase continues the restaurant vertical after the table foreign-key hotfix. It hardens the table/order workflow rather than adding unrelated UI features.

## Changes
- Added explicit restaurant order-line lifecycle statuses: `new`, `sent`, `preparing`, `ready`, `served`, `cancelled`.
- Added `update_line_status` gateway/repository operations for local and remote mode.
- Added `mark_payment_pending` workflow before table close.
- Prevented payment request for empty tables.
- Prevented payment request and table close while unsent `new` order lines exist.
- When closing a valid session, sent/preparing/ready lines are finalized as `served` and the table returns to `free`.
- Added a touch UI action: `Request payment`.
- Added Arabic, English, and German translations for the new workflow/status keys.
- Removed hard dependency from restaurant ad-hoc order lines to the generic `items` table so manually entered restaurant lines do not fail in fresh/partial databases.

## Validation
- `architecture_guard`: passed.
- `pytest`: passed, 13 tests.
- `compileall`: passed.
