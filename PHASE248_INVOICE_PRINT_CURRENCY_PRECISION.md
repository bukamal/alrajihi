# PHASE 248 — Invoice Print Currency Precision

## Scope
Fix browser HTML invoice printing so it respects the display/document currency and never leaks binary float or Decimal residue into printed invoices.

## Why
A Windows print screenshot showed invoice rows and totals like:

- `300000.0000000000000000`
- `549999.99999999999999999999`
- `1E-22-`

The UI was displaying the active currency as Syrian pound (`SYP` / `ل.س`), but printed monetary values did not consistently include the displayed currency symbol.

## Changes
- Added Decimal-based money formatting in `alrajhi_client/printing/print_templates.py`.
- Added currency symbol support for `SYP`, `USD`, `SAR`, `EUR`, `GBP`, `AED`, `QAR`, `KWD`, and `OMR`.
- Invoice print now uses the document currency when present (`currency`, `currency_code`, or `display_currency`), otherwise the active display currency from settings.
- The print template formats amounts only; it does **not** convert invoice amounts, because transaction documents already send display-currency values.
- Tiny residue such as `1E-22-` is normalized to zero before rendering.
- Quantities and percentages are formatted separately from money.
- Invoice meta now includes the printed currency label, e.g. `SYP ل.س`.
- `SettingsService.get_printing_settings()` now exposes currency formatting metadata through the same settings/API contract used by network clients.

## Verification
- `print_templates.py` compiles.
- `settings_service.py` compiles.
- Added `tests/test_phase248_invoice_print_currency_precision_contract.py`.
- Guarded against raw float residue and accidental currency conversion.
