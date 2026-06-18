# Phase 65 — Transaction Document Foundation

Implemented a conservative standalone transaction document layer without expanding `views/dialogs/invoice_dialog.py`.

New core files:
- `features/transactions/transaction_context.py`
- `features/transactions/transaction_document_tab.py`
- `features/transactions/grids/transaction_column_schema.py`
- `features/transactions/grids/transaction_line_model.py`
- `features/transactions/grids/transaction_line_grid.py`
- `features/transactions/grids/transaction_grid_preferences.py`
- `features/transactions/documents/sales_invoice_tab.py`
- `features/transactions/documents/purchase_invoice_tab.py`

Scope: foundation only. Existing invoice and return dialogs remain untouched as legacy fallback.
