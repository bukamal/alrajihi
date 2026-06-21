# Phase 308 — Cafe Sizes & Modifiers

## Scope

Cafe mode now supports a focused drink customization layer on top of the existing restaurant order-line and modifier contracts. It does not introduce a separate cafe order engine.

## Implemented

- Added `cafe_size_modifier_policy` for deterministic cafe order type, default sizes, size-group detection, and modifier normalization.
- Added `RestaurantService.add_cafe_line(...)` to create a normal restaurant order line and attach size/add-on modifiers to the same line.
- Added a touch-safe cafe customization dialog in the restaurant POS for cafe quick orders.
- Size is stored as a restaurant line modifier with action `size`.
- Add-ons are stored as normal restaurant line modifiers with action `add`.
- Modifier totals remain part of restaurant line totals and session balance.
- Kitchen ticket line notes now include preparation notes and modifier labels.
- Restaurant order totals use `line_total` when modifier pricing exists.
- Added Arabic, English, and German labels for cafe sizes and add-ons.
- Registered Phase 308 in the release gate.

## Guardrails

- Cafe stays inside restaurant: no separate cafe tables, invoices, print engine, or currency logic.
- Prices remain Decimal/string values and are displayed through existing currency policies.
- Printing and KOT consume normal restaurant line payloads with modifier notes.
- Existing restaurant and cafe quick-order behavior remains compatible.
