# Phase 51 — BOM Validation Hotfix

## Problem
Saving a manufacturing BOM crashed with:

```text
AttributeError: 'BOMDialog' object has no attribute 'qty_error'
```

## Root cause
`BOMDialog.save()` used `self.qty_error` in `FormValidator.positive(...)`, but the error label was never created in the dialog form.

## Fix
Added `self.qty_error = make_error_label()` immediately after `qty_spin`, and inserted it into the form layout.

## Additional guard
Added:

```text
tools/form_validation_guard.py
```

This checks form validation error-label attributes ending with `_error` and prevents using them before initialization.

## Validation

```text
compileall: PASS
architecture_guard: PASS
reports_contract_check: PASS
phase32_invoice_flow_guard: PASS
offline_read_guard: PASS
offline_widget_guard: PASS
form_validation_guard: PASS
```
