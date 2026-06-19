# Phase 237 — Browser HTML Print Rendering Fix

## Scope

This phase fixes the weak browser print output observed in Windows, where print buttons opened a temporary HTML file showing an emergency fallback page such as `Report Html` and the message that the full print template was not available.

## Root cause

The print service was already routed through a unified print button contract, but the runtime template loader could cache a failed `print_templates` import and keep using the emergency renderer. In frozen Windows builds, template files may exist under PyInstaller's `_MEIPASS` root while package imports resolve through the top-level `printing` package. That made some report/table print buttons open browser HTML, but with fallback content instead of the full branded template.

A second issue was that `print_templates.py` imported `settings_service` at module import time. In constrained/test/frozen import ordering, that could pull the database layer and PyQt dependencies too early, increasing the chance of falling back to the emergency template.

## Changes

- Hardened `printing/_template_loader.py`:
  - checks package imports and PyInstaller `_MEIPASS` file locations;
  - does not permanently cache failed template lookups;
  - registers loaded file modules under both `printing.print_templates` and `alrajhi_client.printing.print_templates`;
  - removes the visible emergency fallback message from browser output;
  - provides a table-capable emergency report renderer if the real module is genuinely unavailable.

- Hardened `printing/print_templates.py`:
  - removed unused `config.get_company_info` import;
  - lazy-loads `settings_service` only when rendering needs settings;
  - can render basic templates even if the full application settings layer is not available during early import.

- Enforced browser HTML as the visible print-button route:
  - `printing_service.print_button_mode()` resolves visible print buttons to `browser`;
  - invoice, return, report, BOM, barcode and table print buttons now open generated HTML in the browser;
  - barcode label printing through settings also uses browser HTML rather than a Qt print dialog.

- Updated printing settings defaults:
  - default print button mode is `browser`;
  - barcode default printer no longer falls back to `pdf:default`.

## Guard

Added:

```bash
python tools/phase237_browser_html_print_guard.py
```

The guard verifies:

- real print templates load from source/runtime;
- browser report output does not show fallback text;
- invoice, return and BOM templates render full HTML tables;
- default visible print mode is browser HTML;
- barcode label print settings route through the same print button renderer;
- PyInstaller frozen template locations are included in the loader.
