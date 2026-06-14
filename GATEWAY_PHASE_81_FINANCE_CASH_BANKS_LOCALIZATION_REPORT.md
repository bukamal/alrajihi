# GATEWAY PHASE 81 – Finance / Cash / Banks Localization

## Scope
Localized the finance-related UI layer to the centralized language system:

- Cashboxes and bank accounts
- POS shifts and financial movements
- Receipt/payment/expense vouchers
- Voucher dialog and validation messages
- Customers list and edit dialog
- Suppliers list and edit dialog

## Languages
Arabic remains the source/default language. German and English translations were added for the same UI keys.

Supported language order:

1. Arabic – RTL
2. German – LTR
3. English – LTR

## Files changed

- `alrajhi_client/i18n/translator.py`
- `alrajhi_client/views/widgets/cashboxes_widget.py`
- `alrajhi_client/views/widgets/vouchers_widget.py`
- `alrajhi_client/views/widgets/customers_widget.py`
- `alrajhi_client/views/widgets/suppliers_widget.py`
- `tools/verify_language_phase81_finance.py`

## Safety constraints

No accounting logic was changed.
No database schema was changed.
No runtime event filters were added.
No QtWebEngine flags were added.
Internal voucher/cashbox values remain stable (`receipt`, `payment`, `expense`, `cash`, `bank`).

## Validation

Passed:

- `python3 -m compileall -q alrajhi_client tools`
- `python3 tools/verify_language_foundation.py`
- `python3 tools/verify_language_migration_phase77.py`
- `python3 tools/verify_language_phase78_sales_purchases_returns.py`
- `python3 tools/verify_language_phase79_inventory_items.py`
- `python3 tools/verify_language_phase80_manufacturing.py`
- `python3 tools/verify_language_phase81_finance.py`

## Notes

The finance screens now use the centralized translation system for the main labels, buttons, table headers, dialogs, validation messages, and print actions. Existing dynamic names from the database, such as customer names, supplier names, branch names, cashbox names, and bank names, are intentionally not translated.
