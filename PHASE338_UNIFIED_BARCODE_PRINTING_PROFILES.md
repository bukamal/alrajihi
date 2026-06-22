# Phase 338 — Unified Barcode Printing Profiles

This phase turns barcode label printing into a profile-driven contract shared by materials, apparel, restaurant and cafe workflows.

## Scope

- Adds `printing/barcode_profiles.py` as the settings/profile bridge for label printing.
- Keeps all label output on the existing Browser HTML path.
- Defines profile settings roots for:
  - `items.default`
  - `apparel.variant_labels`
  - `restaurant.menu_items`
  - `restaurant.table_labels`
  - `cafe.products`
  - `cafe.modifier_labels`
- Adds profile-aware options and normalization so each sector can print single or multi-label batches.
- Apparel labels print variant barcode/variant details and do not fall back to the parent material barcode when variant barcode data exists.
- Restaurant table labels can use QR-only payloads.
- Settings expose profile-specific controls for variant fields, table zone, cafe size and modifier group.

## Contract

Barcode printing is not allowed to become a screen-specific island. Screens call the same `printing_service.barcode_profile_labels_*` entry points and the service resolves profile settings, normalizes rows and renders HTML through `BarcodeLabelService`.
