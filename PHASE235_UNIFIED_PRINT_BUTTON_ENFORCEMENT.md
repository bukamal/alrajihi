# Phase 235 — Unified Print Button Enforcement

## Goal
Replace separate preview/PDF/export print buttons in transaction and barcode workflows with one unified print action that uses the project printing settings and the centralized `printing_service` HTML pipeline.

## Changes

- Transaction document tabs now expose one bottom print action only.
- Removed the transaction document bottom actions for preview, PDF, and save-and-print.
- Legacy transaction `workspace_export()` calls route to `workspace_print()` instead of PDF export.
- Invoice action components no longer call `save_invoice_pdf()` from export.
- Legacy invoice dialog print menu was replaced with one direct unified print action.
- Return document actions now route export to print.
- Return dialog/list print menus no longer expose PDF actions.
- Batch barcode print dialog no longer exposes PDF/PNG pseudo-printers in the visible printer selector.
- Batch barcode printing now uses a single `barcode_labels_print(...)` path.
- Material document label printing now uses `barcode_labels_print_settings(...)`, which reads the project barcode print settings.
- Table/report/voucher print menus no longer expose `export_pdf` actions.
- Legacy PDF methods remain in `printing_service` for compatibility and internal migration safety, but UI buttons no longer expose them.

## New PrintingService helpers

- `barcode_default_printer_name()`
- `barcode_labels_print_settings(...)`

These keep barcode printing tied to project settings while avoiding visible PDF/PNG pseudo-printer buttons.

## Guard

Added:

- `tools/phase235_unified_print_button_guard.py`

The guard blocks:

- PDF actions in UI menus/buttons.
- Transaction document bottom PDF/preview/save-and-print actions.
- Invoice export calling `save_invoice_pdf()`.
- Batch barcode printing using PDF/PNG branches.
- Material label print not using project barcode settings.

## Validation

Executed successfully:

- `python tools/phase235_unified_print_button_guard.py`
- `python tools/phase233_full_unification_guard.py`
- `python tools/phase232_project_language_audit.py`
- `python tools/phase234_dashboard_cashbox_runtime_guard.py`
- `python tools/phase234_ui_finance_workflow_guard.py`
- `python tools/phase227_database_pyinstaller_guard.py`
- `python tools/phase226_printing_runtime_loader_guard.py`
- `python tools/phase224_windows_release_matrix_guard.py`
- `python tools/reports_contract_check.py`
- `python tools/advanced_runtime_test.py`
- `python -m compileall -q alrajhi_client alrajhi_server`
