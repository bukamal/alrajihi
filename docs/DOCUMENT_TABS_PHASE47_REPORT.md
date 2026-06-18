# Phase 47 — Invoice, Return, and Voucher Document Tabs

## Scope
This phase extends the document-tab model beyond items/categories into the most used transactional documents:

- Sales invoices
- Purchase invoices
- Sales returns
- Purchase returns
- Receipt/payment/expense vouchers

## Architecture
A migration adapter `DialogDocumentTab` was added for large legacy dialogs. It hosts legacy dialogs inside the workspace as first-class document tabs while exposing the common workspace contract:

- `workspace_save()`
- `workspace_print()`
- `workspace_export()`
- `can_close()`
- dirty-state tracking

This keeps the UX consistent now and allows later decomposition into smaller components without breaking the workflow.

## Converted Flows
- Invoice list create/edit now opens `InvoiceEditorTab`.
- Return list create/edit now opens `SalesReturnEditorTab` or `PurchaseReturnEditorTab`.
- Voucher list create/edit now opens `VoucherEditorTab`.

## Notes
Invoice internals still need deeper decomposition into Header/Lines/Totals/Payments components. This phase makes invoices tab-native first, then prepares the next safe refactor.
