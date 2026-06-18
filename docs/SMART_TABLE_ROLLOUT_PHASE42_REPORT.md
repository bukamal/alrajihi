# Phase 42 — SmartTableView Rollout

## Scope

This phase expands the unified `SmartTableView` from the first management tabs to the wider ERP workspace.
The migration targets list/report/management screens while leaving intentionally editable grids such as POS and return-line editors on `QTableWidget`.

## Converted widgets

- Audit log
- Base management widget
- Branches
- Cashboxes and banks
- Categories
- Dashboard alert table
- Sales/purchase invoice lists
- Manufacturing BOM/order lists
- Reports tables
- Returns list/history tables
- Users
- Vouchers
- Warehouses/balances/movements/transfers

## Shared behavior now available

- Context-menu copy
- Excel export
- Print/preview through the central printing service
- Column visibility menu
- Column layout persistence/reset
- Local filter support for pages that opt in
- Selection mapping support when proxy filtering is enabled

## Guard

Added `tools/smart_table_rollout_guard.py` to prevent management/list widgets from reintroducing direct `CustomTableView` usage.

## Explicit non-goals

This phase does not convert editable operational tables such as POS order lines, returns line editors, or monitoring grids.
Those require a separate delegate/model migration because replacing them mechanically would risk behavior regressions.
