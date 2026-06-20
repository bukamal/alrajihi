# PHASE268_POS_THERMAL_RECEIPT_PRINT_UNIFICATION

## Scope

This phase fixes POS thermal receipt printing after the project-wide document/list/report/operational shell unification.

The user-reported issue was visible in browser HTML thermal output:

- POS receipt reused the invoice print path too directly.
- Receipt amounts were shown using the display currency label while still carrying storage/base values.
- The thermal receipt header suppressed the company logo unconditionally.
- The receipt layout still carried too many A4 invoice columns for thermal paper.
- POS receipt options existed partially in settings but were not enforced consistently by the print template.

## Changes

### Dedicated POS receipt template path

Added `pos_receipt_html()` in:

- `alrajhi_client/printing/print_templates.py`

Added PrintingService entry points:

- `PrintingService.pos_receipt_html()`
- `PrintingService.pos_receipt_print()`
- `PrintingService.pos_receipt_browser()`

`POSWidget._offer_print_receipt()` now calls `printing_service.pos_receipt_print(...)` instead of `invoice_print(..., paper='thermal80')`.

### Currency correction

POS invoices are persisted in storage/base currency by `POSService`, while the cashier sees display currency.

The new POS receipt path converts POS persisted values to the receipt/display currency before formatting:

- line unit price
- line total
- subtotal
- discount
- tax
- grand total
- paid
- remaining

The conversion is limited to the explicit POS receipt path and does not alter normal invoice/return printing, which already sends display amounts.

### Thermal logo/header unification

Thermal templates no longer hide the logo unconditionally.

The thermal header now respects settings:

- `printing/show_logo`
- `printing/thermal/show_logo`
- `pos/receipt_show_logo`

Logo data still comes from the same company/settings contract introduced in Phase 241, including `company/logo_data_uri` for client/server deployments.

### POS settings contract

Added POS receipt settings keys:

- `pos/receipt_show_logo`
- `pos/receipt_show_qr`

These are exposed in `PosSettingsTab` and surfaced through `SettingsService.get_printing_settings()`.

### Thermal column simplification

POS thermal receipts now use a compact line table:

- #
- item
- quantity
- price
- total

instead of the full A4 invoice columns such as barcode, unit, discount %, tax %, etc.

## Validation

Added:

- `tests/test_phase268_pos_thermal_receipt_unification.py`

Full test result:

- `234 passed`
- `1 warning`
- `0 failed`
