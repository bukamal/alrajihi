# Phase 59 - HTML Print Numeric + Browser Action Hotfix

## Fixed

- `InvoiceDialog._invoice_print_payload()` now converts monetary values to `Decimal` before computing remaining balance.
- `_build_invoice_print_payload()` now uses the same safe Decimal conversion.
- `PrintingService.invoice_browser()` was added as a stable public alias to `invoice_browser_preview()`.
- Duplicate imports in `printing_service.py` were cleaned.

## Root cause

- `QDoubleSpinBox.value()` returns `float`, while invoice totals are `Decimal`.
- The browser print action expected `PrintingService.invoice_browser()`, but only `invoice_browser_preview()` existed.

## Validation

- `compileall`: PASS
- `architecture_guard`: PASS
- `phase32_invoice_flow_guard`: PASS
- `offline_read_guard`: PASS
- `offline_widget_guard`: PASS
- `print_action_guard`: PASS
- `html_print_expansion_guard`: PASS
- targeted print numeric/action checks: PASS

Note: `qt_signal_method_guard` has pre-existing false positives for inherited Qt methods such as `accept`, `reject`, and `showMinimized`, so it was not used as a blocking check for this hotfix.
