# Phase 222 — Expense Document Shell Refactor

## Objective

Convert the expense workflow from a thin `VoucherEditorTab(type=expense)` wrapper into a first-class expense document shell, matching the document UX direction used by transaction documents, party documents, and voucher documents.

## Changes

### Expense-specific document shell

`alrajhi_client/features/finance/documents/expense_document_tab.py` was rebuilt around `BaseDocumentTab` instead of inheriting `VoucherEditorTab`.

The expense screen now has:

- `ExpenseDocumentHeaderCard`
- `ExpenseIdentityPanel`
- `ExpenseDocumentPanel`
- `ExpenseSummaryPanel`
- `ExpenseBottomActionBar`
- `_ExpenseMetricCard`

The UI no longer exposes voucher type selection, party linkage, supplier/customer selectors, or invoice linkage. It is now explicitly an expense document.

### Preserved backend compatibility

Persistence remains compatible with the voucher backend:

- `type = expense`
- `customer_id = None`
- `supplier_id = None`
- `invoice_id = None`

Saving and updating still go through `voucher_service.add/update`, so cashbox/bank movement behavior and printing compatibility remain intact.

### Expense-specific finance policy

`VoucherService` now routes expense vouchers to expense-specific operations:

- create -> `expense_create`
- edit -> `expense_edit`
- delete -> `expense_delete`
- view -> `expense_view`

This removes the earlier double-permission behavior where the expense UI required expense permission but the service still required the generic voucher permission.

### Currency and payment handling

The document reuses `VoucherPaymentPanel`, preserving the Phase 218 display/base currency contract:

- display amount is shown in display currency
- payload amount is converted back to storage/base currency
- payment target is cashbox or bank account

### i18n

Added Phase 222 translation keys for Arabic, German, and English:

- `expense_document_subtitle`
- `expense_identity_panel`
- `expense_payment_panel`
- `expense_summary_panel`
- `expense_metric_amount`
- `expense_metric_payment_method`
- `expense_metric_target`
- `expense_metric_date`
- `expense_metric_reference`
- `expense_reference_placeholder`
- `expense_description_placeholder`
- `expense_description_required`
- `expense_shell_unified`

### Guards

Added:

- `tools/phase222_expense_document_shell_guard.py`

Updated:

- `tools/phase221_voucher_document_shell_guard.py`
- `tools/phase219_projectwide_architecture_audit.py`

## Validation

Executed successfully:

```bash
python tools/phase222_expense_document_shell_guard.py
python tools/phase221_voucher_document_shell_guard.py
python tools/phase220_party_document_shell_guard.py
python tools/phase219_projectwide_architecture_audit.py
python tools/phase218_currency_consistency_guard.py
python tools/phase217_printing_i18n_guard.py
python tools/phase216_legacy_dialog_audit_guard.py
python tools/phase215_settings_workspace_consolidation_guard.py
python tools/phase214_reports_governance_guard.py
python tools/phase212_runtime_stabilization_guard.py
python tools/reports_contract_check.py
python tools/advanced_runtime_test.py
python -m compileall -q alrajhi_client alrajhi_server
```

## Result

Expense entry/editing is now structurally aligned with the invoice-style document philosophy: explicit header, body panels, payment panel, summary panel, and bottom actions — without relying on a generic voucher editor surface.
