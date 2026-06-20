# Phase 242 — Browser HTML Print Unification + Print Language Hardening

## Scope
This phase continues the printing repair after company/logo/network settings were unified in Phase 241.
It enforces one visible printing path: generated HTML opened in the system browser.

## Changes
- Routed legacy `preview_html`, `print_html`, `save_pdf`, and `render_html` to `open_html_in_browser`.
- Removed Qt print dialogs / Qt preview / Qt PDF rendering from `printing_service.py`.
- Converted barcode label direct/PDF entry points to the browser HTML path.
- Converted legacy `PrintManager` to a browser-only compatibility shim.
- Converted legacy `PDFPrinter` barcode methods to browser HTML.
- Converted `ThermalPrinter.print_label` and `ThermalPrinter.print_receipt` to browser HTML so visible project printing remains HTML-based.
- Hardened template translation so printable documents use `settings_service.print_language()` instead of the global UI language.
- Made emergency fallback labels Arabic/German/English aware.

## Network / multi-user note
Printing continues to consume settings through `settings_service`, which uses the active `SettingsGateway`.
In client/server mode, company identity, logo data URI, print template, and print language are read across the API boundary with local cache fallback.

## Verification
- Static tests added in `tests/test_phase242_browser_html_print_unification_i18n.py`.
- `compileall` passed for client/server/tests in the patch environment.
