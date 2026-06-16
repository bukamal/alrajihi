# Phase135 External Management Table Columns

Scope: external management/list tables only.

## Applied

### Sales invoices external table
Columns now follow:
- Reference
- Invoice
- Invoice Value
- Customer
- Paid
- Received
- Remaining
- Invoice Profit
- Date
- Notes

### Purchase invoices external table
Columns now follow:
- Reference
- Invoice
- Invoice Value
- Supplier
- Paid
- Remaining
- Date
- Notes

### Sales returns external table
Columns now follow the matching management structure:
- Reference
- Return No.
- Original Invoice
- Customer
- Return Value
- Refunded
- Settlement Remaining
- Date
- Notes

### Purchase returns external table
Columns now follow the matching management structure:
- Reference
- Return No.
- Original Invoice
- Supplier
- Return Value
- Returned Amount
- Settlement Remaining
- Date
- Notes

## Notes
- Existing CustomTableView identities were preserved.
- Column show/hide remains driven by the current table column customization system.
- No database schema change was introduced.
- Calculations use the existing invoice/return service values.
- Added Arabic, English and German labels for new column keys.

## Verification
- `python3 -m compileall -q alrajhi_client` passed.
- Translation keys checked for Arabic, English and German.
