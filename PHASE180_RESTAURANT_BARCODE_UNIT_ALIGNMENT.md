# Phase 180 — Restaurant Barcode / Unit Alignment

This phase aligns Restaurant POS with the unified material barcode and unit barcode pipeline introduced for materials, invoices, returns, and POS.

## Key changes

- `RestaurantService` now uses `barcode_input_service` through `add_entry()`.
- Scanner-like input is exact-only and does not fall back to the first menu search result.
- Unit barcode metadata is preserved on restaurant order lines:
  - `unit_id`
  - `unit`
  - `conversion_factor`
  - `base_qty`
  - `barcode_scope`
  - `matched_barcode`
- Local and remote restaurant gateways accept the same metadata.
- Client and server restaurant schemas were expanded safely with ALTER TABLE guards.
- Restaurant POS Return key now distinguishes between manual menu search and scanner input.
- Restaurant order line labels show unit barcode context and base quantity when applicable.
- Arabic/German/English translations were added for the new restaurant barcode behavior.

## Architectural rule

Restaurant POS must not implement its own barcode logic. It must pass barcode-like input through `RestaurantService.add_entry()` and the unified `barcode_input_service`.
