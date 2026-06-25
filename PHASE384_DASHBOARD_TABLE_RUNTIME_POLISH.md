# Phase 384 — Dashboard & Table Runtime Polish

## Scope

This phase applies a targeted runtime polish requested after the inline/menu
unification work:

- Remove colored label backgrounds from the dashboard where labels were creating
  visual noise.
- Remove the Monitoring shortcut from the daily shortcuts card.
- Keep all daily shortcut button captions centered.
- Standardize Enter traversal for editable grids: Enter opens, commits and moves
  to the next operational cell; material/item remains the first entry column;
  material/barcode commits move to quantity.
- Stop clearing existing/default cell values while navigating with Enter.
- Center display and editor data across editable grids and list tables.

## Runtime policy

- Navigation never erases data by itself. Editors select text so a real new input
  naturally replaces the value, but moving through the grid does not clear it.
- QLineEdit table editors are centered.
- Runtime visual polish installs a center display delegate for table views and
  normalizes existing QTableWidgetItem alignment.
- Editable grid cell selection is preserved even when runtime visual polish is
  applied.

## Guard

`tools/phase384_dashboard_table_runtime_polish_guard.py`
