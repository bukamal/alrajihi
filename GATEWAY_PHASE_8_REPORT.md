# Gateway Phase 8 Report

## Scope
Phase 8 converts reporting access to the unified Gateway pattern without changing report formulas or accounting behavior.

## Added files
- `alrajhi_client/gateways/reporting_gateway.py`
- `alrajhi_client/gateways/local/reporting_gateway.py`
- `alrajhi_client/gateways/remote/reporting_gateway.py`

## Modified files
- `alrajhi_client/core/services/reporting_service.py`

## New flow
```text
UI / Dashboard / Reports
→ ReportingService
→ ReportingGateway
→ Remote API or Local ReportingDAO
```

## Local behavior
Local mode still uses `ReportingDAO`, but only inside:

```text
gateways/local/reporting_gateway.py
```

## Remote behavior
Remote mode uses the existing server report endpoints through `RestClient`:

- `/api/reports/summary`
- `/api/reports/income_statement`
- `/api/reports/balance_sheet`

The following methods are not yet exposed on the server API, so the remote gateway returns safe empty results instead of using direct SQL:

- `customer_statement`
- `supplier_statement`
- `trial_balance`

## Validation
- `compileall`: passed
- ZIP integrity test: passed

## Remaining direct DAO references in core/services
- `inventory_service.py` → `InventoryMovementDAO`
- `manufacturing_service.py` → `manufacturing_dao`

## Recommendation
Next phase should handle `InventoryService` carefully. It is higher risk because inventory movements affect stock quantities, valuation, invoices, returns, warehouses, and manufacturing.
