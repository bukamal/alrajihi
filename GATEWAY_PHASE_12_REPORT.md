# Gateway Phase 12 Report

## Scope

Phase 12 moves sales and purchase returns behind Gateway boundaries while preserving the current service public API and existing business behavior.

## Converted modules

- `core/services/sales_return_service.py`
- `core/services/purchase_return_service.py`

## Added gateway contracts

- `alrajhi_client/gateways/sales_return_gateway.py`
- `alrajhi_client/gateways/purchase_return_gateway.py`

## Added local adapters

- `alrajhi_client/gateways/local/sales_return_gateway.py`
- `alrajhi_client/gateways/local/purchase_return_gateway.py`

The local adapters retain the existing local return behavior, including validation, inventory movement calls, warehouse movement calls, cashbox effects, and audit logging.

## Added remote adapters

- `alrajhi_client/gateways/remote/sales_return_gateway.py`
- `alrajhi_client/gateways/remote/purchase_return_gateway.py`

The remote adapters call the existing REST client methods:

- `get_sales_returns`
- `get_sales_return`
- `get_sales_return_invoices`
- `get_sales_returnable_lines`
- `create_sales_return`
- `delete_sales_return`
- `get_purchase_returns`
- `get_purchase_return`
- `get_purchase_return_invoices`
- `get_purchase_returnable_lines`
- `create_purchase_return`
- `delete_purchase_return`

## Architecture guard update

Removed these temporary legacy exceptions from `tools/architecture_guard.py`:

- `alrajhi_client/core/services/sales_return_service.py`
- `alrajhi_client/core/services/purchase_return_service.py`

## Resulting flow

```text
ReturnsWidget
→ SalesReturnService / PurchaseReturnService
→ SalesReturnGateway / PurchaseReturnGateway
→ Remote REST API or Local return adapter
```

## Verification

- `python -m compileall -q alrajhi_client alrajhi_server tools`: passed
- `python tools/architecture_guard.py`: passed
- Remaining direct `DatabaseConnection` exceptions: 6 legacy files

## Not changed intentionally

- No inventory ledger redesign.
- No BOM/manufacturing changes.
- No alteration to return accounting/cashbox rules.
- No schema migration added.

## Recommended next phase

Phase 13 should address remaining legacy `DatabaseConnection` exceptions by separating infrastructure/status functions from normal business flows, starting with `audit_service` or backup/settings utilities.
