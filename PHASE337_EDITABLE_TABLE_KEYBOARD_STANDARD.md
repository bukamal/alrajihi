# Phase 337 — Editable Table Keyboard Standard

This phase standardizes keyboard entry behavior across ERP editable grids without adding business logic to UI widgets.

## Scope

- `Enter` starts editing the current editable cell.
- `Enter` after editor commit advances to the next editable visible cell.
- `Shift+Enter` moves to the previous editable visible cell.
- At the end of transaction-like models that expose `add_empty_line()`, the table appends a new line and focuses the first editable visible cell.
- `Esc` remains application-owned for the dashboard shortcut, except when Qt's native editor is actively cancelling an edit.

## Integration

The shared policy is implemented in:

- `alrajhi_client/ui/table_keyboard_policy.py`

It is installed in:

- `alrajhi_client/views/custom_table_view.py`
- `alrajhi_client/ui/editable_smart_grid.py`

Because `SmartTableView`, transaction grids, POS grids, restaurant grids, cafe grids, apparel grids, and multiple legacy editor grids inherit from these base widgets, the behavior now has one centralized implementation.

## Guardrails

The policy does not access repositories, services, gateways, printing, or settings directly. It only uses Qt model/view APIs and optional `add_empty_line()` hooks exposed by editable line models.
