# Phase 240 — Invoice / Return Browser HTML Payload Fix

## Problem

Users reported that browser print output for invoice and return documents showed a raw Python payload, for example:

```text
Invoice Html
{'id': ..., 'type': ..., Decimal('...'), 'lines': [...]}
```

and return documents behaved the same way.

That means the visible print button reached the emergency template fallback rather than a structured document renderer.  In a frozen Windows build this can happen when PyInstaller fails to load `printing.print_templates` at runtime.  The previous emergency renderer was intentionally weak and exposed `str(payload)`.

## Fix

`alrajhi_client/printing/_template_loader.py` now includes structured emergency renderers for:

- `invoice_html`
- `return_html`

The fallback path now renders:

- localized Arabic document title
- document metadata table
- invoice/return line table
- totals table
- notes section

It no longer prints raw dictionaries, `Decimal(...)`, `<pre>`, or technical titles such as `Invoice Html` / `Return Html`.

## Scope

This protects all invoice and return print buttons that call:

- `printing_service.invoice_print(...)`
- `printing_service.return_print(...)`
- `TransactionPrintingBridge.print()`
- legacy callers routed through the unified print path

It also protects PyInstaller/frozen builds if the real template module cannot be imported for any reason.

## Guard

Added:

```text
tools/phase240_invoice_return_browser_html_guard.py
```

The guard validates both:

1. Real template path.
2. Emergency fallback path.

It fails if browser HTML contains:

```text
'id':
"id":
Decimal(
<pre
Invoice Html
Return Html
قالب طباعة احتياطي
```

## Validation

Executed successfully:

```text
python tools/phase240_invoice_return_browser_html_guard.py
python tools/phase237_browser_html_print_guard.py
python tools/phase236_print_settings_contract_guard.py
python tools/phase235_unified_print_button_guard.py
python tools/phase239_business_scenario_reconciliation_guard.py
python -m compileall -q alrajhi_client alrajhi_server
```
