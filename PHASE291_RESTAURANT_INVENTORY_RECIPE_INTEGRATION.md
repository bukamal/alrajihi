# Phase 291 — Restaurant Inventory Recipe Integration

## Scope

This phase hardens restaurant inventory consumption at checkout and at explicit recipe-consumption calls.
It keeps the restaurant workflow separate from the manufacturing workflow while allowing menu items to consume real stock components.

## Implemented

- Added `features.restaurant.restaurant_inventory_recipe_policy` for shared restaurant component-consumption arithmetic and idempotency keys.
- Hardened local restaurant recipe consumption so it now records both:
  - `restaurant_inventory_consumption` audit rows.
  - `inventory_movements` rows with movement type `restaurant_consume`.
- Added manufacturing BOM fallback when a menu item has no restaurant-specific recipe:
  - restaurant recipe has priority;
  - manufacturing BOM is used only when no restaurant recipe is configured;
  - BOM conversion factor and waste percentage are respected.
- Preserved idempotency by `source_key`; repeated consumption does not double-decrement stock.
- Kept operational inventory quantity current by decrementing `items.quantity` only after the unique consumption row is inserted.
- Added compatibility columns on `restaurant_inventory_consumption`:
  - `source_type`
  - `movement_id`
  - `unit_cost`
  - `warehouse_id`
- Added `restaurant_consume` to stock recalculation semantics so future item recalculations treat restaurant consumption as an outbound movement.
- Mirrored the same consumption hardening in the server-side restaurant repository.

## Behavior

When a restaurant session is checked out:

1. The sales invoice is created.
2. The order lines are converted to invoice lines.
3. Recipe/BOM components are consumed once.
4. Inventory movements are posted for configured component items.
5. The session is closed and the table is released.

If no recipe or BOM exists for a sold restaurant item, checkout is not blocked. The item is reported as skipped without recipe so configuration can be completed later.

## Verification

- `tests/test_phase291_restaurant_inventory_recipe_integration.py`
- Existing Phase 34 recipe/modifier tests remain compatible.
