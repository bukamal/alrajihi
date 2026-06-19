# Phase 219 — Project-wide Architecture / UX Audit

## Scope

This phase performs a project-wide scan after the tab/document migration phases. It checks whether primary workflows still bypass the tab system or remain form-stack screens instead of professional document shells.

The scan covers:

- legacy `QDialog` classes and direct `.exec()` calls
- dashboard quick actions and main workflow entry points
- tab/document conversion status
- UI/feature imports of database/gateway layers
- direct `QSettings` use in feature/UI layers
- known high-risk workflows: customers, suppliers, receipt/payment vouchers, expenses, POS, restaurant, manufacturing, inventory, reports

## Result summary

The audit tool produced:

- high: 2
- medium: 90
- low: 1
- inventory-only legacy definitions: 13

The number of medium findings is intentionally conservative because it flags every remaining modal dialog execution outside low-level dialog modules. Many of these are acceptable small utility dialogs, but they must be classified explicitly.

## Critical conclusion

The project has mostly moved from windows to tabs, but not every tab has the same professional document structure as the invoice/transaction documents.

The main gaps are:

1. `VoucherEditorTab` is technically a tab and uses decomposed panels, but it is still a vertical form stack. It does not yet have the same document shell structure used by invoices: header, body area, contextual side/summary panel, and bottom action bar.
2. `ExpenseDocumentTab` currently inherits the voucher form stack and only fixes the type to `expense`. It should become a first-class expense document shell or use a finance document shell.
3. `PartyEditorTab` for customer/supplier is a tab with context tables, but it is still not a unified master-data document shell. It needs a stronger layout: identity/contact/credit panels, account context, bottom actions, and responsive behavior.

## Hotfix applied in this phase

Dashboard voucher quick action no longer opens `VoucherDialog` directly.

Old behavior:

```text
Dashboard -> VoucherDialog -> exec()
```

New behavior:

```text
Dashboard -> MainWindow.open_quick_voucher() -> VoucherEditorTab / ExpenseDocumentTab
```

Also, `MainWindow.open_quick_voucher('expense', voucher=existing_expense)` now routes to `open_expense_document(expense_id)` instead of opening the generic voucher tab for an existing expense.

## Specific user-reported areas

### Customer / Supplier creation

Current status:

```text
PartyEditorTab exists
Uses BaseDocumentTab
Uses party_operation_policy
Uses service layer
```

Gap:

```text
Still form/tabbed-context style, not the same professional document shell as invoices.
```

Recommended next phase:

```text
Phase 220 — Party Document Shell Refactor
```

Target structure:

```text
Header: Customer/Supplier name, type, save status
Main: identity/contact/tax/credit panels
Context: statement, invoices, vouchers grids
Side: balance/credit summary
Bottom actions: New, Save, Save & Open Statement, Print Statement, Close
```

### Receipt / Payment vouchers

Current status:

```text
VoucherEditorTab exists
Uses BaseDocumentTab
Uses VoucherHeaderPanel / VoucherLinkPanel / VoucherPaymentPanel / VoucherActionsPanel
Uses finance_operation_policy
```

Gap:

```text
Still vertical form-stack; not invoice-like shell.
```

Recommended next phase:

```text
Phase 221 — Finance Voucher Document Shell Refactor
```

Target structure:

```text
Header: voucher type, number, date, status
Body: party/invoice/payment panels
Side: amount, remaining, cashbox/bank, currency summary
Bottom actions: New, Save, Save & Print, PDF, Close
```

### Expense document

Current status:

```text
ExpenseDocumentTab exists
Inherits VoucherEditorTab
Locks type = expense
Uses expense-specific finance_operation_policy
```

Gap:

```text
Structurally it is still a voucher form-stack with type locked.
```

Recommended next phase:

```text
Phase 222 — Expense Document Shell Refactor
```

Target structure:

```text
Header: expense number/date/status
Body: expense category, account/cashbox/bank, amount, notes, attachment placeholder
Side: currency/payment summary
Bottom actions: Save, Save & Print, PDF, Close
```

## Remaining legacy dialog categories

### Allowed utility dialogs

These can remain dialogs if documented:

```text
LoginDialog
ActivationDialog
ChangePasswordDialog
BarcodeCameraDialog
Column chooser / filter builder
Print dialogs / file dialogs
Small confirmation/picker dialogs
```

### Legacy fallback dialogs

These should stay only as fallback until fully removed:

```text
InvoiceDialog
AddEntityDialog
ItemDialog
BOMDialog
ProductionOrderDialog
ProductionDetailsDialog
SalesReturnDialog
PurchaseReturnDialog
VoucherDialog
BranchDialog
CashboxDialog
BankDialog
UserDialog
```

No primary workflow should instantiate these directly.

## Audit artifacts

Generated files:

```text
tools/phase219_projectwide_architecture_audit.py
tools/audit_outputs/phase219_projectwide_architecture_audit.json
tools/audit_outputs/PHASE219_PROJECTWIDE_ARCHITECTURE_AUDIT.md
```

## Recommended execution order

```text
Phase 220 — Party Document Shell Refactor
Phase 221 — Finance Voucher Document Shell Refactor
Phase 222 — Expense Document Shell Refactor
Phase 223 — Restaurant Modal Shell Cleanup
Phase 224 — Inventory Adjustment / Stock Movement Document Tab
Phase 225 — Final Legacy Dialog Allowlist Guard
```
