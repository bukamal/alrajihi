# Phase 247 — Print template f-string syntax hotfix

## Problem

The Windows executable reached the browser HTML print bootstrap, but the real template module failed to load with:

```text
PRINT-TEMPLATE-BOOTSTRAP-UNAVAILABLE
SyntaxError: f-string: unmatched '(' (print_templates.py, line 548)
```

This means packaging was no longer the primary failure.  The packaged `print_templates.py` file itself contained an invalid nested double-quoted expression inside an f-string.

## Root cause

The invoice QR HTML line used a double-quoted f-string while also calling `_tr("print_document_qr")` inside the expression:

```python
qr_html = f"... {_s(_tr("print_document_qr"))} ..."
```

Python parses the inner `"` as ending the outer f-string, causing a startup-time template import failure in the packaged app.

## Fix

The translated QR label is now computed before the f-string:

```python
qr_label = _s(_tr("print_document_qr"))
qr_html = f"<table class='qr-table'><tr><td><img src='{qr_uri}'><div>{qr_label}</div></td></tr></table>"
```

This removes nested quoting from the f-string and keeps the QR label translated through the print-language setting.

## Network / multi-user / i18n impact

No local-only setting was introduced.  The fix keeps the existing settings-driven language behavior intact:

- Arabic print language remains RTL.
- English and German print languages remain LTR.
- Company, logo, paper, and print settings remain sourced through `SettingsService` / `SettingsGateway`.
- Browser HTML remains the only print output path.

## Validation

Added `tests/test_phase247_print_template_fstring_syntax_hotfix.py` to ensure:

1. `print_templates.py` compiles with `py_compile`.
2. `invoice_html()` can be imported and executed without emitting `PRINT-TEMPLATE-BOOTSTRAP-UNAVAILABLE`.
3. The invoice QR branch no longer contains nested `_tr("...")` calls inside the f-string.
4. The QR label still uses the translated `print_document_qr` key.

