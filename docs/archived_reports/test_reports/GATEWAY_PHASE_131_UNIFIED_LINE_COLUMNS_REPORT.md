# Phase131 — Unified invoice/return line columns

Implemented:

- Sales invoice line table default visible columns:
  barcode, item name, quantity, unit, price, total, notes, item profit.
- Purchase invoice line table default visible columns:
  barcode, item name, unit, quantity, price, total, notes.
- Sales return line table default visible columns:
  barcode, item name, return quantity, unit, price, total, notes.
- Purchase return line table default visible columns:
  barcode, item name, unit, return quantity, price, total, notes.

Additional details:

- Existing technical columns such as previous returned, returnable quantity, discount, tax, row number, and delete are still available and can be shown/hidden through the columns context menu.
- Column visibility/order is persisted using QSettings under the project table preferences flow.
- Return line totals recalculate from the entered return quantity and selected unit.
- Invoice sales item profit is calculated per line from displayed sale price minus item cost converted by selected unit factor.
- Labels are available in Arabic, English, and German.

Validation:

- python -m compileall -q alrajhi_client: PASS
