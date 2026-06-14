# GATEWAY PHASE 86 — ftranslate Hotfix

## Scope
Fix startup warnings preventing sales and purchase invoice pages from loading:

- `sales_invoices`: `name 'ftranslate' is not defined`
- `purchase_invoices`: `name 'ftranslate' is not defined`

## Root Cause
`invoices_widget.py` contained two calls to a non-existent helper `ftranslate(...)` introduced during localization migration. The project translation API uses `translate(...)`, which already supports keyword formatting.

## Changes
- Replaced both pagination label calls from `ftranslate(...)` to `translate(...)`.
- Added `tools/verify_no_ftranslate.py` guard to detect undefined `ftranslate` references.

## Validation
- `python3 tools/verify_no_ftranslate.py` ✅
- `python3 -m compileall -q alrajhi_client tools` ✅
