# Phase 236 — Print Settings Contract Audit

## Purpose

This phase verifies and enforces the contract between every visible print button and the project printing settings.

The rule is now:

- UI exposes one print button only.
- UI does not choose preview/browser/direct/PDF per screen.
- The print action, paper/template, language, header/footer, typography, barcode label options and barcode printer are resolved by `settings_service` and `printing_service`.
- Barcode single/multiple printing uses the same settings-driven route as the material print button.
- No visible PDF/PNG print/export paths remain in invoice, return, barcode or table/report printing buttons.

## Key changes

- Added `PrintingService.print_button_mode()` and `_print_button_render()`.
- All `*_print()` domain methods now render through the configured project print-button mode instead of hardcoding preview/direct behavior.
- `barcode_default_printer` now defaults to system print dialog instead of `pdf:default`.
- Barcode settings UI filters out PDF/image pseudo-printers.
- `BatchPrintDialog` no longer has a per-dialog printer/PDF/image selector and calls `barcode_labels_print_settings()`.
- Table toolbar, reports, vouchers, returns, inventory, manufacturing and restaurant visible print buttons now use one print path.
- The material label preview button was removed from UI; the unified material print button remains the print contract.

## Guards

Added:

- `tools/phase236_print_settings_contract_audit.py`
- `tools/phase236_print_settings_contract_guard.py`

The audit output is written to:

- `tools/audit_outputs/phase236_print_settings_contract_audit.json`
- `tools/audit_outputs/PHASE236_PRINT_SETTINGS_CONTRACT_AUDIT.md`

## Validation

Executed successfully:

- `python tools/phase236_print_settings_contract_guard.py`
- `python tools/phase235_unified_print_button_guard.py`
- `python tools/phase233_full_unification_guard.py`
- `python tools/phase232_project_language_audit.py`
- `python tools/phase228_ui_printing_guard.py`
- `python tools/phase227_database_pyinstaller_guard.py`
- `python tools/phase226_printing_runtime_loader_guard.py`
- `python tools/phase224_windows_release_matrix_guard.py`
- `python tools/reports_contract_check.py`
- `python tools/advanced_runtime_test.py`
- `python -m compileall -q alrajhi_client alrajhi_server`
