# Phase 339 — Barcode Multi-Print UI for Items/Apparel/Restaurant/Cafe

This phase connects the Phase 338 barcode profile contract to actual operator-facing UI flows.

Implemented scope:

- Kept the legacy material `BatchPrintDialog` class name, but upgraded it to accept a `profile_id`.
- Added one unified multi-print candidate adapter in `printing/barcode_multi_print.py`.
- Supported profile-aware batch sources for:
  - `items.default`
  - `apparel.variant_labels`
  - `restaurant.menu_items`
  - `restaurant.table_labels`
  - `cafe.products`
  - `cafe.modifier_labels`
- Apparel workspace now exposes selected-variant and batch variant barcode printing.
- Restaurant shell now exposes menu-item barcode printing and table QR/barcode printing.
- Cafe shell now exposes cafe-product barcode printing and cafe-modifier barcode printing.
- All UI entries still route through `printing_service.barcode_profile_labels_print`, which opens Browser HTML only.
- Apparel labels use variant barcode/color/size/variant code; they do not print the parent material barcode when a variant barcode is present.

This is intentionally a UI binding phase, not a new print renderer.
