# Phase137 Logical Columns Cleanup

## Scope
- Clean external management tables from line-item columns.
- Keep line-item columns inside invoice/return dialogs only.
- Preserve existing column visibility/settings system.
- Preserve Arabic/English/German translation keys already used by the unified table headers.

## Applied changes
- Removed line-detail lookup/update from external invoice tables.
- Removed line-detail lookup/update from external returns tables.
- External tabs now remain management summaries:
  - Sales: reference, invoice, invoice value, customer, paid, received, remaining, invoice profit, date, notes.
  - Purchases: reference, invoice, invoice value, supplier, paid, remaining, date, notes.
  - Sales returns: reference, return no, original invoice, customer, return value, refunded, settlement remaining, date, notes.
  - Purchase returns: reference, return no, original invoice, supplier, return value, returned amount, settlement remaining, date, notes.
- Dialog line tables retain contextual line columns and column visibility controls.

## Tests
PASS:
- compileall: alrajhi_client, alrajhi_server, tools
- phase137_logical_columns_guard
- phase125_returns_unit_delegate_delete_guard
- phase32_invoice_flow_guard
- invoice_units_guard
- returns_unit_columns_deep_test_phase124
- phase118_no_top_info_cards_guard
- qt_signal_method_guard
- html_print_expansion_guard
- verify_phase89_secondary_localization
- vouchers_deep_accounting_test_phase105
- invoice_price_edit_deep_test_phase106
- invoice_phase108_integrity_guard
- manufacturing_numeric_guard
- manufacturing_deep_regression_test
- offline_read_guard
- offline_ui_guard
- offline_widget_guard
- print_action_guard

## Note
Runtime GUI boot was not executed because PyQt5 is not installed in this sandbox. Static, accounting, migration-independent, printing, localization, and business-logic guards above passed.
