# Phase 415 — Unified Sales Invoice Grid Runtime

This phase stops treating the editable invoice grid as a static source-code problem and moves the sales invoice line-entry behavior into a clean, testable runtime contract.

## Scope

- `TransactionLineGrid` now installs the standard Enter editor filter from every editor creation path, including `AnyKeyPressed`, double-click editing, and programmatic focus.
- `TransactionLineModel` owns line lifecycle through `ensure_single_trailing_empty_line()`.
- `add_empty_line()` is now idempotent: it reuses the current trailing blank row instead of creating duplicate blank rows.
- `StandardTableKeyboardMixin` delegates trailing-row creation to the model lifecycle gate when available.
- `unified_grid_navigation_policy.py` defines the Qt-free sales invoice route and row-lifecycle invariants so they can be tested without a GUI runtime.

## Sales Invoice Enter Route

The official route is:

`item -> unit -> qty -> price -> discount -> tax -> total -> notes -> next row item`

The route is semantic. It does not depend on physical column indexes and it skips hidden columns by resolving against visible keys.

## Critical Fix

The previous engine mostly worked only when Enter itself opened the editor. In real usage, Qt can open an editor through typing or mouse interaction before the table-level handler runs. Phase 415 hooks the editor-opening path itself, so the Enter filter is installed for real operator workflows.

## Row Lifecycle Rule

There may be at most one reusable blank row at the bottom of the transaction grid. Any append request must pass through the model's idempotent lifecycle gate.
