# Phase 138-A/B Reports Foundation + Party Statements

## Scope
- Introduced a first reports-center foundation without changing accounting sources.
- Improved customer and supplier account statements to include true opening balances and running balances.
- Added saved table identities for report tables so column visibility/order/width are persistent through the existing table preferences system.
- Added a report summary bar and reset-filters action.
- Kept unified printing path through the existing printing service.
- Added Arabic, English, and German labels for new report controls and statement source types.

## Accounting rule applied
- Customer balance increases by sales invoices and decreases by sales returns/receipt vouchers.
- Supplier balance increases by purchase invoices and decreases by purchase returns/payment vouchers.
- When a date range starts after earlier transactions, earlier transactions are accumulated into an Opening Balance row before period rows.

## Tests
- `python3 -m compileall -q alrajhi_client`: PASS
- `pytest -q tests/test_phase138_reporting_statements.py`: PASS
- Translation key presence check for ar/en/de: PASS

## Notes
- GUI interaction was not executed because PyQt5 is not installed in this environment.
- No independent UI-side financial recalculation was added; reports still read through the reporting service/DAO path.
