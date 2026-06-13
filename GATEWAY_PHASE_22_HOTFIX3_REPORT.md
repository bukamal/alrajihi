# Gateway Phase 22 Hotfix 3

## Problem
In remote/client mode `InvoiceService` created the invoice through the server API, then still called `warehouse_service.record_invoice_movements()` from the desktop.

That was wrong because the server `/api/invoices` endpoint already persists invoice lines and inventory movements transactionally.

Observed effects:
- Purchase invoice may affect quantities through remote movement paths while UI visibility is inconsistent.
- Offline sale invoice can crash because, after queueing `/api/invoices`, the client tries to call `/api/warehouses/movements` while disconnected.
- Risk of duplicate inventory effect in client/server mode.

## Fix
Added `InvoiceService._client_side_movements_enabled()`.

Client-side warehouse movement posting/reversal now runs only when the active invoice gateway is local.

Remote/client mode now delegates invoice stock effects exclusively to the server invoice API.

## Files changed
- `alrajhi_client/core/services/invoice_service.py`

## Validation
- `python3 -m compileall -q alrajhi_client alrajhi_server`
- `python3 tools/architecture_guard.py`
- zip integrity test
