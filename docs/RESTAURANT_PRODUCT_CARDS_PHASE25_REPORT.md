# Phase 25 — Restaurant Product Cards

## Scope
Added a touch-first menu/product-card ordering layer on top of the Phase 24 restaurant UI.

## Implemented
- Added `RestaurantGateway.list_menu_items(...)` across abstract/local/remote gateways.
- Local and server implementations read product cards from the canonical `items` catalog.
- Added server endpoint `GET /api/restaurant/menu_items` backed by `RestaurantRepository.list_menu_items(...)`.
- Added search field and touch product-card grid to `RestaurantPOSWidget`.
- Added manual item fallback for restaurants that have not yet populated the item catalog.
- Preserved Arabic RTL and German/English LTR layout support.
- Added Phase 25 translations and QSS styling.

## Validation
- `architecture_guard` passed.
- `pytest` passed: 20 tests.
- `compileall` passed.
- Cache directories removed after validation.

## Remaining restaurant work
- Convert restaurant session to real sales invoice/payment.
- Add kitchen display screen (KDS).
- Add table transfer/merge/split bill.
- Add product category tabs and restaurant modifiers.
