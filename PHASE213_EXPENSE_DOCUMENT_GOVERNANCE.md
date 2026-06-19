# Phase 213 — Expense Document / Governance

- Added expense-specific finance operations and RBAC keys.
- Added `ExpenseDocumentTab`, an explicit tabbed expense document built on the voucher engine but fixed to type `expense`.
- Added `MainWindow.open_expense_document()` and routed quick expense creation through the tabbed workspace.
- Hardened `ExpenseService` behind `finance_operation_policy` instead of leaving legacy expense access ungoverned.
- Added dashboard quick action for expenses.

The legacy expense-shaped records remain backed by voucher data for compatibility; no DAO/REST access was introduced in UI code.
