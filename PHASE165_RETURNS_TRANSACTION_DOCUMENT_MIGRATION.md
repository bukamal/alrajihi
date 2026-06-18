# Phase 165 — Returns Transaction Document Migration

## Scope

Phase 165 moves sales and purchase returns into the same transaction document surface introduced for invoices. The legacy return dialogs remain available as fallback through feature flags, but the new path now uses:

- `TransactionContext`
- `TransactionColumnSchema`
- `TransactionLineModel`
- `TransactionLineGrid`
- `TransactionDocumentTab`

## Added contexts

- `sales_return_context()`
- `purchase_return_context()`

These contexts define party role, direction, price mode, and stock policy for returns.

## Added return schemas

`transaction_column_schema.py` now contains:

- `sales_return_schema()`
- `purchase_return_schema()`

Return schemas include original invoice reference, original quantity, previous returned quantity, returnable quantity, return quantity, reason, unit price/refund, restock marker, total, and notes.

## Added documents

```text
alrajhi_client/features/transactions/documents/sales_return_tab.py
alrajhi_client/features/transactions/documents/purchase_return_tab.py
```

These tabs are thin document-type wrappers around `TransactionDocumentTab`.

## Service behavior

Return persistence remains behind the existing services:

- `sales_return_service.create_return/update_return`
- `purchase_return_service.create_return/update_return`

The new UI does not bypass existing accounting, stock, warehouse, or cashbox logic.

## Routing

`MainWindow.open_return_document()` now tries the new transaction return tabs first when feature flags allow it. If import or creation fails, it falls back to:

- `SalesReturnEditorTab`
- `PurchaseReturnEditorTab`

## Feature flags

```python
features/use_new_transaction_returns = true
features/use_new_transaction_returns_for_existing = true
```

## Important notes

- `invoice_dialog.py` was not expanded.
- Legacy return dialogs remain present and operational.
- Return editing still delegates to existing service-level `update_return()`, which reverses and recreates the accounting document as before.
- Advanced return unit selection delegates from the legacy dialog were not migrated yet; Phase 166 should focus on unit delegates and stronger source-invoice line editing behavior.
