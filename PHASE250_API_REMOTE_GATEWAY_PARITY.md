# PHASE250_API_REMOTE_GATEWAY_PARITY

## Scope

This phase starts the API/remote parity track after the Document Shell contract audit.
It fixes the confirmed client/server gap for sales and purchase return editing.

## Changes

- Added `RestClient.update_sales_return(...)` and `RestClient.update_purchase_return(...)`.
- Added `RemoteSalesReturnGateway.update_return(...)`.
- Added `RemotePurchaseReturnGateway.update_return(...)`.
- Updated local gateway remote branches to call the server PUT endpoints instead of emulating update with DELETE+POST on the client.
- Added server endpoints:
  - `PUT /api/returns/sales/<id>`
  - `PUT /api/returns/purchase/<id>`
- Server update uses the accounting-safe reversal/recreate pipeline, preserving return number and original invoice unless the payload explicitly overrides the return number.

## Network and multi-user notes

The routes remain JWT-protected and scoped by `get_jwt_identity()`. A user can only update returns belonging to their own user scope. The update does not mutate historical inventory/cash effects in place; it cancels the old return and creates a replacement record to keep ledger semantics explicit.

## Language, settings and permissions

No UI labels were changed in this phase. The existing i18n keys for return update remain in use. The change is at the API/gateway parity layer so the Document Shell can rely on a consistent `update_return` contract in local and client/server modes.

## Verification

- Remote return gateway classes are instantiable despite abstract `update_return` contract.
- RestClient exposes PUT methods.
- Server routes expose PUT endpoints.
- Targeted phase tests pass.
