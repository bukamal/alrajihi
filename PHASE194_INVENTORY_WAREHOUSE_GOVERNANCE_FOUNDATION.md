# Phase 194 — Inventory / Warehouse Governance Foundation

This phase starts the same unification path for inventory and warehouses that was
applied to invoices, materials, POS, restaurant, and manufacturing.

## Scope

- Added `settings_service.get_inventory_settings()` as a broader inventory contract.
- Added `inventory_operation_policy` for warehouse, transfer, ledger, movement, and reconciliation operations.
- Routed `WarehouseService` critical methods through the policy.
- Routed `InventoryService` ledger/direct movement tools through the policy.
- Added inventory RBAC permission keys and migration inserts.
- Added basic WarehousesWidget button-state enforcement.

## Important boundary

Automatic inventory postings from invoices, returns, POS, restaurant, and
manufacturing remain allowed as system postings. Direct manual movements and
ledger maintenance are governed separately.
