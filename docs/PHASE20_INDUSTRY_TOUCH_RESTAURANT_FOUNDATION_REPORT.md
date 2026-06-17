# Phase 20 — Industry, Touch Mode, Restaurant Foundation

## Scope

This phase introduces the extension foundation for vertical business profiles:

- `general`
- `pharmacy`
- `restaurant`
- `apparel`
- `mixed`

It also adds a first-class `ui/mode` setting with `classic`, `touch_pos`, and `compact`, plus a restaurant table/session/KOT schema boundary.

## Implemented

- Server `IndustryRepository` and `/api/industry/profile`.
- Server `RestaurantRepository` with tables, sessions, order lines, kitchen tickets.
- Thin API wrappers for `industry` and `restaurant`.
- Client `IndustryService` and local/remote gateways.
- Client `RestaurantService` and local/remote gateways.
- Touch-ready restaurant dashboard skeleton under `views/restaurant`.
- Arabic, German, and English translation keys for the new vertical UI terms.

## Architectural rule

HTTP layers remain SQL-free. SQL is owned by repositories only.

## Next safe phases

1. Integrate `RestaurantDashboard` into the main navigation when `industry/profile == restaurant` or `mixed`.
2. Add full restaurant POS line editor and split bill workflow.
3. Add apparel `item_variants` and pharmacy `item_batches` modules.
