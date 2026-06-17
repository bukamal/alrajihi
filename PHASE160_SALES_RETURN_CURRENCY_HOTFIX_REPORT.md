# Phase 160 - Sales Return Currency Display Hotfix

## Problem
Sales return line price and line total could show unrealistic numbers when invoice-line monetary values from upgraded/legacy data were already stored in the invoice/original currency but the return dialog treated them as USD and converted them again to the display currency.

Typical symptom: SYP display values become multiplied by the exchange rate again.

## Fix
- Added return-line monetary normalization in `alrajhi_client/views/widgets/returns_widget.py`.
- Added explicit invoice currency metadata to returnable sales lines in:
  - `alrajhi_client/gateways/local/sales_return_gateway.py`
  - `alrajhi_server/api/returns.py`
- Added the same metadata for purchase returnable lines for consistency.
- The UI now prefers explicit `unit_price_usd` / `line_currency` metadata when present.
- Added a high-rate legacy guard for SYP-like currencies to avoid double conversion.

## Validation
- `python -m compileall -q alrajhi_client alrajhi_server tools` passed.
- `python tools/architecture_guard.py` passed.

## Notes
This fixes price/total display calculation in the return dialog and protects remote/local returnable-line payloads from currency ambiguity.
