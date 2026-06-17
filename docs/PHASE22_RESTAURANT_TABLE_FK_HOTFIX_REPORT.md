# Phase 22 — Restaurant Table FK Hotfix

## Problem
Clicking a restaurant table could raise `FOREIGN KEY constraint failed` on a fresh database.

## Root Cause
The Phase 21 table map rendered 12 placeholder table buttons when `restaurant_tables` was empty. Those placeholders had ids `1..12`, but no persisted rows existed yet. Opening a placeholder attempted to insert a `restaurant_sessions.table_id` value that did not reference a real `restaurant_tables.id` row.

## Fix
- `LocalRestaurantGateway.list_tables()` now seeds 12 real default tables when the restaurant table table is empty.
- `RestaurantRepository.list_tables()` applies the same server-side seed behavior.
- `open_table()` now validates that the target table exists and is active before inserting a session.
- Missing tables now raise a clear `ValueError` instead of letting SQLite raise a raw FK error.

## Verification
- `architecture_guard`: passed.
- `pytest`: 10 passed, 1 pre-existing warning.
- `compileall`: passed.
- Added regression tests for first-click table opening with SQLite foreign keys enabled.
