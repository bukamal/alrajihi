# Gateway Phase 22 Report

## Scope

Phase 22 introduces a non-destructive Inventory Ledger foundation.

## Added

- `inventory_ledger` table in client/server migrations.
- `InventoryLedgerDAO` for local append-only ledger access.
- InventoryGateway methods:
  - `ledger_entries()`
  - `record_ledger_entry()`
  - `ledger_balance()`
- Remote REST client methods for the new ledger endpoints.
- Server API endpoints:
  - `GET /api/inventory-ledger`
  - `POST /api/inventory-ledger`
  - `GET /api/inventory-ledger/balance`

## Safety

This phase does not replace existing `inventory_movements`, `warehouse_movements`, or `item_warehouse_balances`. It does not recalculate current stock from the ledger yet.

## Next

Phase 23 should start dual-writing selected low-risk inventory events into `inventory_ledger`, beginning with manual `InventoryService.record_movement()` only.
