# Phase 173 — Material Workspace Professionalization

This phase upgrades the materials list/workspace so it follows the same governance rules introduced for transaction documents.

## Main changes

- `ItemsWidget` no longer imports or opens the legacy `ItemDialog`.
- The materials list now uses a schema-driven column model from `features/items/material_list_schema.py`.
- The grid supports business presets:
  - compact
  - cashier
  - warehouse
  - accountant
  - manager
- The materials list adds filters for category, item type, and stock status.
- Cost/value columns are role-aware and are hidden/masked when cost/profit visibility is restricted.
- Barcode print actions use the existing `BatchPrintDialog` / barcode label pipeline and now check `ACTION_PRINT_BARCODES`.
- Editing materials uses the item-specific permission `ACTION_EDIT_ITEMS` instead of the old invoice edit permission fallback.
- Generic table preferences now use `settings_service` instead of raw `QSettings`, scoped by user, branch, and active settings profile.
- Remote material sold quantities are now backed by `/api/items/sold-quantities`, so the materials grid is no longer forced to show zeros in API mode.

## Architectural rule

Material master data remains under the item/product service and gateway contract internally, but Arabic UI terminology remains `المادة / المواد`.

## Validation

Run:

```bash
python tools/phase173_material_workspace_guard.py
python -m compileall -q alrajhi_client alrajhi_server
```
