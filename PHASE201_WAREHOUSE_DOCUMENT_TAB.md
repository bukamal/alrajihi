# Phase 201 — Warehouse Document Tab

## Goal
Convert add/edit warehouse from an inline `QDialog` inside `WarehousesWidget` into a real workspace tab, and fix the wrong field label that showed the material/item name label for warehouse name.

## Changes
- Added `features/inventory/documents/warehouse_document_tab.py`.
- Exported `WarehouseDocumentTab` from `features.inventory`.
- Added `MainWindow.open_warehouse_document(warehouse_id=None)`.
- Updated `WarehousesWidget.add_warehouse()` and `edit_warehouse()` to open tabs first, with the legacy dialog as fallback.
- Corrected legacy fallback label from `item_name_label` to `warehouse_name_label`.
- Added Arabic/German/English i18n keys for warehouse document labels.
- Added a guard for the migration.

## Architecture
The new tab uses:
- `BaseDocumentTab`
- `warehouse_service`
- `branch_service`
- `inventory_operation_policy`
- `i18n.translate`

It does not import DAO, REST, database, or `QSettings` directly.
