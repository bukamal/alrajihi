# Phase 160 - QTableWidgetItem Ownership Hotfix

## Problem
Qt printed repeated warnings:

`QTableWidget: cannot insert an item that is already owned by another QTableWidget`

## Root cause
In `alrajhi_client/views/widgets/returns_widget.py`, the return edit loader reused an existing `QTableWidgetItem` from `dialog.lines_table.item(...)` and called `setItem(...)` on it again. Qt treats an item already attached to a table as owned, so reinserting it triggers the warning.

## Fix
Changed the update logic to:

- Reuse existing item only by editing its text/data/flags.
- Call `setItem(...)` only when the cell has no item yet.
- Applied to sales/purchase return edit loader cells:
  - unit column
  - return quantity column

## Validation
- `python -m compileall -q alrajhi_client alrajhi_server tools`
- `python tools/architecture_guard.py`

Both passed.
