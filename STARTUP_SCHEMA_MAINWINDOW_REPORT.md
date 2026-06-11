# Startup schema guard + MainWindow invoice split

## Applied changes

1. `alrajhi_client/database/connection.py`
   - Added a runtime schema guard inside `DatabaseConnection.get_connection()`.
   - When the local SQLite connection is opened, `apply_common_schema()` now runs automatically before repositories execute queries.
   - This protects old databases from missing-column errors such as `warehouse_id`, `branch_id`, `cashbox_id`, `bank_account_id`, `payment_method`, and `shift_id`.

2. `alrajhi_client/views/main_window.py`
   - Removed the legacy `InvoicesWidget` import from `MainWindow`.
   - Kept only `SalesInvoicesWidget` and `PurchaseInvoicesWidget`.
   - `MainWindow.init_pages()` now explicitly creates two independent pages:
     - `sales_invoices`
     - `purchase_invoices`
   - The old `invoices` route remains only as a compatibility redirect to `sales_invoices`; it no longer creates a combined invoices page.

## Validation

- `python3 -m compileall alrajhi_client alrajhi_server`: passed.
- SQLite old-database schema upgrade test with a minimal old `invoices` table: passed.
- ZIP integrity test: passed.
