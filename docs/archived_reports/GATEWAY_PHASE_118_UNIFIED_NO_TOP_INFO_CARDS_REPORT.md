# Phase118 — Unified No Top Info Cards

Applied a project-wide UI rule: content pages must not create explanatory/header cards at the top of the page.

## Scope
- Disabled `ModernPageHeader` insertion in `apply_modern_widget` for all widgets.
- Added runtime cleanup of legacy `ModernPageHeader` if an older widget instance/layout still contains it.
- Removed the custom Settings top explanatory card so the page starts directly with tabs.
- Removed the Monitoring top title/explanatory block and hid the old summary placeholder.
- Preserved functional toolbars, filters, tables, section cards, dashboard content cards, and dialog headers. These are functional UI elements, not page-level explanatory cards.
- Reconciled localization import guards with direct `alrajhi_client/main.py` execution mode by avoiding absolute `alrajhi_client.*` imports in widgets.

## Validation
- `python3 -m compileall -q alrajhi_client alrajhi_server`: PASS
- `tools/verify_no_absolute_alrajhi_imports.py`: PASS
- `tools/verify_phase89_secondary_localization.py`: PASS
- `tools/verify_pos_localization_phase88.py`: PASS
- `tools/phase112_voucher_pos_ui_guard.py`: PASS
- `tools/qt_signal_method_guard.py`: PASS
- `tools/offline_widget_guard.py`: PASS
- `tools/html_print_expansion_guard.py`: PASS
- `tools/phase61_brand_print_dashboard_guard.py`: PASS
- `tools/invoice_phase108_integrity_guard.py`: PASS
- `tools/vouchers_deep_accounting_test_phase105.py`: PASS
- `tools/manufacturing_deep_regression_test.py`: PASS
- `tools/phase118_no_top_info_cards_guard.py`: PASS

## Result
The UI behavior is now unified: content pages do not show top explanatory/header cards. The remaining cards are functional content/sections, not duplicated page headers.
