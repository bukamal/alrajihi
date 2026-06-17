# Phase133 External Table Columns

Scope: external interface tables, not dialog line tables.

Updated:
- Sales invoices external table.
- Purchase invoices external table.
- Sales returns external table.
- Purchase returns external table.

Added line-related columns where missing:
- Barcode.
- Item name.
- Quantity.
- Unit.
- Price.
- Line total.
- Notes.
- Item profit for sales only.

Preserved existing document-level columns:
- Reference/return number.
- Date.
- Customer/supplier.
- Invoice totals/payment columns.

Behavior:
- Columns are available in the external tables.
- Visibility remains controlled through the existing CustomTableView/TableToolbar column preferences.
- Settings are saved by table identity.
- Arabic, English, and German translation keys added for new total labels.

Technical notes:
- invoice detail loading now includes item barcode/cost fields.
- return detail loading now joins item data so external return tables can show item names/barcodes instead of IDs.

Validation:
- python compileall passed for alrajhi_client.
