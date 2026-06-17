# Restaurant Modifiers + Recipes Phase 34

## Scope

This phase adds a professional restaurant modifier and recipe-consumption foundation on top of Phase 33.

## Added capabilities

- Modifier groups per menu item or globally.
- Modifier options with price delta, kitchen labels, defaults, and optional linked item.
- Order-line modifiers with action semantics: add, remove, note, size.
- Modifier-aware line totals and session subtotal.
- Modifier notes included in kitchen/invoice representation.
- Restaurant recipe/BOM table independent from manufacturing internals.
- Recipe component lines with quantity, unit, component item, and unit cost.
- Idempotent restaurant inventory consumption ledger.
- Optional quantity deduction from component items when component_item_id is available.
- Checkout integrates invoice posting and recipe consumption without duplicate consumption.

## New server endpoints

- GET `/api/restaurant/menu_items/<item_id>/modifier_groups`
- POST `/api/restaurant/modifier_groups`
- POST `/api/restaurant/modifier_groups/<group_id>/options`
- GET `/api/restaurant/lines/<line_id>/modifiers`
- POST `/api/restaurant/lines/<line_id>/modifiers`
- GET `/api/restaurant/menu_items/<item_id>/recipe`
- POST `/api/restaurant/menu_items/<item_id>/recipe`
- POST `/api/restaurant/sessions/<session_id>/recipe_consumption`

## Architectural notes

- SQL remains inside gateway/repository boundaries.
- HTTP routes only delegate to repository methods.
- Client service/gateway interfaces were extended for Local and Remote modes.
- Inventory consumption uses a `source_key` uniqueness rule to prevent double deduction.

## Validation

- `python tools/architecture_guard.py` passed.
- `python tools/phase32_invoice_flow_guard.py` passed.
- `python tools/phase32_windows_import_guard.py` passed.
- `pytest` passed: 39 tests.
- `compileall` passed for runtime packages, tools, and tests.
