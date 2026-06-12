# Gateway Phase 9 Report — Inventory Movements

## Scope

Phase 9 converts the legacy inventory movement boundary from direct DAO access to the unified Gateway pattern.

This phase is intentionally limited to `InventoryService` and legacy `inventory_movements`. It does **not** redesign the warehouse ledger, invoice posting, stock valuation, or manufacturing logic.

## Files Added

- `alrajhi_client/gateways/inventory_gateway.py`
- `alrajhi_client/gateways/local/inventory_gateway.py`
- `alrajhi_client/gateways/remote/inventory_gateway.py`

## Files Modified

- `alrajhi_client/core/services/inventory_service.py`
- `alrajhi_client/database/connection_rest.py`
- `alrajhi_server/api/items.py`

## New Application Flow

```text
UI / Repositories
→ InventoryService
→ InventoryGateway
→ Local InventoryMovementDAO or Remote REST API
```

## Remote API Added

- `GET /api/items/<item_id>/inventory-movements`
- `POST /api/inventory-movements`

These endpoints preserve the existing legacy semantics of `InventoryMovementDAO`:

- insert into `inventory_movements`
- recalculate `items.quantity`
- recalculate `items.average_cost`

## Verification

- Python compile check passed for client and server.
- No direct `InventoryMovementDAO` import remains in `core/services`.
- DAO access is now confined to `gateways/local/inventory_gateway.py`.

## Important Note

This is still the old inventory movement model. The strategic next step remains a formal inventory ledger discipline, but this phase prepares that work by placing all legacy movement calls behind a replaceable gateway boundary.
