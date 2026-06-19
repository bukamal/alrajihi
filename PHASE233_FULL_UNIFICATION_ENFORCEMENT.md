# Phase 233 — Full Unification Enforcement

## Scope

This phase starts the full unification track across the project and enforces three contracts:

1. UI currency display/input must not hard-code `USD`.
2. All Qt printing primitives must remain inside the centralized `alrajhi_client/printing` package.
3. Visible UI text must be routed through `translate()`, `tr()`, or `_tr()` so Arabic/German/English display language is respected.

## Currency unification

Updated UI-facing currency conversions in `alrajhi_client/views` and `alrajhi_client/features` so direct conversion calls no longer use hard-coded `USD` for persisted/base values.

Examples of the new contract:

- `currency.storage_currency()` for persisted/base amounts.
- `currency.to_display(...)` or `currency.convert(..., currency.storage_currency(), display_curr)` for UI display.
- `currency.from_display(...)` or `currency.convert(..., display_curr, currency.storage_currency())` for UI input before persistence.
- Settings screens may still list literal currency codes such as `USD`, `SAR`, and `SYP` because those are domain choices, not display conversion leaks.

## Printing unification

Added a Phase 233 guard that blocks direct Qt printing primitives outside the central printing package. This keeps project screens on the unified HTML printing path through `printing_service` / printing bridges.

Allowed printing internals remain isolated under:

- `alrajhi_client/printing/printing_service.py`
- `alrajhi_client/printing/print_manager.py`
- `alrajhi_client/printing/thermal_printer.py`
- other files inside `alrajhi_client/printing/`

## Language unification

Migrated remaining visible text findings from the earlier project UI language audit. The broad client-wide visible-text scan now reports zero findings.

Areas cleaned include:

- main startup/network dialogs
- activation dialog
- splash screen
- batch barcode printing dialog
- column/customizer and category dialogs
- reports status labels
- settings tabs and controls
- backup/status/security profile summaries
- printing settings and label designer controls
- action handler menu actions

## New guard

Added:

- `tools/phase233_full_unification_audit.py`
- `tools/phase233_full_unification_guard.py`

The guard fails CI if it finds:

- `currency.convert(..., 'USD', ...)` in client UI code
- visible UI text not routed through translation APIs
- Qt print primitives outside the printing package
- missing `printing_service.render_html(...)`

## Verification

Executed successfully:

- `python tools/phase233_full_unification_guard.py`
- `python tools/phase232_project_language_audit.py`
- `python tools/phase228_ui_printing_guard.py`
- `python tools/phase218_currency_consistency_guard.py`
- `python tools/phase232_dashboard_cashbox_language_guard.py`
- `python tools/phase231_dashboard_decimal_import_guard.py`
- `python tools/phase230_topbar_optional_buttons_guard.py`
- `python tools/phase229_action_placement_guard.py`
- `python tools/phase227_database_pyinstaller_guard.py`
- `python tools/phase226_printing_runtime_loader_guard.py`
- `python tools/phase224_windows_release_matrix_guard.py`
- `python tools/phase219_projectwide_architecture_audit.py`
- `python tools/reports_contract_check.py`
- `python tools/advanced_runtime_test.py`
- `python -m compileall -q alrajhi_client alrajhi_server`
