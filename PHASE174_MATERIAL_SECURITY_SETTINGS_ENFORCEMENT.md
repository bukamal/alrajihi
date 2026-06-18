# Phase 174 — Material Security & Settings Enforcement

## Objective

This phase hardens the new tab-based material editor so it respects the project-wide settings, RBAC/permissions, multi-user security policy, local/remote API boundary, and material activity rules.

The material UI remains tab-based and does not return to `ItemDialog`.

## Implemented

### 1. Material activity summary through service/gateway/API

Added a service-level activity contract:

- `ProductService.item_activity_summary(item_id)`
- `ProductService.item_has_activity(item_id)`
- `ItemGateway.activity_summary(item_id)`
- `LocalItemGateway.activity_summary(item_id)`
- `RemoteItemGateway.activity_summary(item_id)`
- `RestClient.get_item_activity_summary(item_id)`
- `GET /api/items/<item_id>/activity-summary`

The material editor no longer needs to know about invoice, return, inventory, BOM, or production tables.

### 2. Opening quantity lock

`MaterialDocumentTab` now locks opening quantity when the material has operational activity and the material settings say opening quantity must not be edited after activity.

Policy key:

- `prevent_opening_quantity_edit_after_activity`

Source:

- `settings_service.get_material_settings()`

### 3. Cost visibility

Added material cost visibility policy:

- `PermissionService.ACTION_VIEW_ITEM_COSTS`
- RBAC permission: `items.cost.view`
- Material setting: `hide_cost_for_non_admin`

When the user is not allowed to view material costs, the purchase price and margin preview are hidden.

### 4. Opening-stock edit permission

Added:

- `PermissionService.ACTION_EDIT_OPENING_STOCK`
- RBAC permission: `items.opening_stock.edit`

The material editor disables opening quantity when the effective permission is denied.

### 5. Barcode print permission

The material editor now enforces `print_barcodes` before previewing or printing labels.

### 6. Edit permission

The material editor now applies `edit_items` at the tab level:

- widgets become read-only/disabled
- save actions are disabled
- barcode generation/scanning actions that would mutate the material are disabled

### 7. Unit validation

The material editor validates:

- duplicate unit names
- invalid conversion factors
- invalid unit barcodes
- duplicate barcode between the base material and sub-units

Settings added through `get_material_settings()`:

- `require_unique_unit_names`
- `require_unit_barcode_validation`
- `allow_unit_barcode_duplicates`

### 8. Remote route contract

Added required remote route:

- `/api/items/<int:item_id>/activity-summary`

### 9. Guard

Added:

- `tools/phase174_material_security_guard.py`

It verifies that material security and activity checks are service/API-based and not UI-table-based.

## Validation

Executed successfully:

```bash
python -m compileall -q alrajhi_client alrajhi_server
python tools/phase169_system_governance_guard.py
python tools/phase170_barcode_api_guard.py
python tools/phase171_material_document_guard.py
python tools/phase172_unit_barcode_api_guard.py
python tools/phase173_material_workspace_guard.py
python tools/phase174_material_security_guard.py
```

## Architectural rule

Material UI must not query operational tables directly.  All activity, usage, and security decisions must pass through services and gateways.
