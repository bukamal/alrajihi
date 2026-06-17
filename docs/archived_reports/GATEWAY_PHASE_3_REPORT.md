# Gateway Refactor - Phase 3

## Scope

Phase 3 migrates the warehouse service access path to the unified Gateway contract.

## Implemented files

- `alrajhi_client/gateways/warehouse_gateway.py`
- `alrajhi_client/gateways/local/warehouse_gateway.py`
- `alrajhi_client/gateways/remote/warehouse_gateway.py`

## Modified files

- `alrajhi_client/core/services/warehouse_service.py`

## Resulting path

```text
UI / other services
  -> WarehouseService
  -> WarehouseGateway
  -> RemoteWarehouseGateway -> RestClient -> Flask API
     or
  -> LocalWarehouseGateway -> warehouse_dao -> SQLite
```

## Operations now behind the gateway

- warehouse list/get/create/update/archive
- default warehouse lookup
- balances and balance count
- available quantity lookup
- movement listing
- movement recording/reversal
- transfer listing/create/cancel

## Safety notes

- UI code remains unchanged.
- Public method names in `WarehouseService` remain unchanged.
- Existing DAO code remains intact and is now confined to the local adapter.
- Remote mode uses existing `RestClient` methods; no server endpoint changes were introduced.

## Validation

- `python3 -m compileall` passed for the new gateway files and `warehouse_service.py`.
- No remaining direct `warehouse_dao` imports were found in `alrajhi_client/core` or `alrajhi_client/views`.

## Next recommended phase

Phase 4 should not start with full invoices yet. The safer next target is Branch/Cashbox/Bank gateway unification, because those services are foundational for invoices and POS but carry less transactional inventory risk than invoice creation itself.
