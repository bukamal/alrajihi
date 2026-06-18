# Phase 62 — Invoice Table Input UX

## Scope

This phase improves day-to-day invoice and table input ergonomics without changing data access boundaries.

## Invoice grid changes

- Added an invoice-grid shortcuts hint below the extended invoice lines table.
- Added keyboard-first line work:
  - Enter: move to next editable invoice cell.
  - Insert: add line.
  - Ctrl+D: duplicate selected line.
  - Ctrl+L: focus barcode/search input.
  - F4: open invoice column chooser.
  - Ctrl+Shift+F: fit invoice table columns.
  - Escape: return to barcode/search input.
- Kept the bottom action bar and unified printing route intact.

## SmartTableView changes

- Added enterprise keyboard shortcuts:
  - Ctrl+Shift+C: column chooser.
  - Ctrl+Shift+F: fit columns.
  - Ctrl+Alt+F: filters.
  - Ctrl+Shift+S: save view preset.
- Added row density profiles: compact, comfortable, touch.
- Added visible-column and current-source-row helpers for future master/detail and bulk actions.

## Guard

`tools/invoice_table_input_ux_guard.py` prevents regression of these UX capabilities.
