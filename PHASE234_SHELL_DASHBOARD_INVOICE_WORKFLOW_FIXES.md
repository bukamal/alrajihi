# Phase 234 — Shell / Dashboard / Invoice / Workflow Fixes

## Scope
This phase applies targeted UX and data fixes requested after Phase 233.

## Changes
- Moved notifications, theme switch, screenshot, and current-user identity from the hidden compatibility `ModernTopBar` into `UnifiedActionBar`.
- Hid the old top utility bar while keeping it as a compatibility object.
- Hardened dashboard cashbox totals by normalizing cashbox/bank balance fields across local and remote adapters.
- Added a runtime cashbox dashboard guard that creates a default cashbox, records a movement, and verifies the dashboard snapshot includes the movement and balance.
- Removed the duplicated `paid` column from the sales invoice list.
- Fixed sales invoice `received` to prefer `paid_amount` and fall back to legacy `paid`.
- Filled sales invoice `invoice_profit` from `reporting_service.invoice_profit_report()` and respected profit-hiding permissions.
- Hid the entire workflow/posting button block when workflow is disabled in settings.
- Removed the trailing colon from the `original_invoice` label in Arabic, English, and German.

## Guards
- `tools/phase234_ui_finance_workflow_guard.py`
- `tools/phase234_dashboard_cashbox_runtime_guard.py`

## Verification
- `python tools/phase234_dashboard_cashbox_runtime_guard.py`
- `python tools/phase234_ui_finance_workflow_guard.py`
- `python tools/phase233_full_unification_guard.py`
- `python tools/phase232_project_language_audit.py`
- `python tools/phase232_dashboard_cashbox_language_guard.py`
- `python tools/phase231_dashboard_decimal_import_guard.py`
- `python tools/phase230_topbar_optional_buttons_guard.py`
- `python tools/phase229_action_placement_guard.py`
- `python tools/phase228_ui_printing_guard.py`
- `python tools/phase227_database_pyinstaller_guard.py`
- `python tools/phase226_printing_runtime_loader_guard.py`
- `python tools/phase224_windows_release_matrix_guard.py`
- `python tools/phase219_projectwide_architecture_audit.py`
- `python tools/reports_contract_check.py`
- `python tools/advanced_runtime_test.py`
- `python -m compileall -q alrajhi_client alrajhi_server`
