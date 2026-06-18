# Phase 43 — Unified Action Bar + Printing Boundary Preservation

## Scope
This phase adds a shared workspace action bar for high-frequency tab commands while preserving the project's centralized printing model.

## Added
- `alrajhi_client/shell/unified_action_bar.py`
- MainWindow integration via `setup_action_bar()`
- Shared actions: New, Save, Refresh, Print, Export, Quick Open
- `tools/unified_printing_guard.py`
- Phase 43 regression tests

## Printing rule
The action bar does not print directly. It delegates to `MainWindow.print_current_tab()`, which continues to call tab-specific commands. Table printing still flows through:

`SmartTableView / CustomTableView.print_table -> printing.printing_service`

This keeps PDF/preview/direct print behavior unified across reports, tables, and document tabs.

## Verification
- `architecture_guard`: passed
- `phase32_invoice_flow_guard`: passed
- `phase32_windows_import_guard`: passed
- `restaurant_production_readiness_guard`: passed
- `smart_table_rollout_guard`: passed
- `unified_printing_guard`: passed
- `pytest`: 64 passed
- `compileall`: passed
