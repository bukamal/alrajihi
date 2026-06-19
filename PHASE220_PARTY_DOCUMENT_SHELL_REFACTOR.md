# Phase 220 — Party Document Shell Refactor

## Goal

Upgrade the customer/supplier editor from a simple form tab into a document-shell layout aligned with the newer transaction document experience.

## Changes

- Rebuilt `features/parties/party_editor_tab.py` around a document shell:
  - Header card with title, subtitle, refresh, print, export, save.
  - Identity panel.
  - Contact/address panel.
  - Right-side balance and credit summary panel.
  - Related-data tabs for statement, invoices, and vouchers.
  - Fixed bottom action bar.
- Kept persistence behind `EntityService`.
- Kept policy enforcement behind `party_operation_policy`.
- Kept context tables behind `reporting_service`, `invoice_service`, and `voucher_service`.
- Switched related monetary displays to `currency.format_base_amount()` so they follow the unified storage/display currency contract.
- Added party shell translation keys for Arabic, German, and English.
- Added `tools/phase220_party_document_shell_guard.py` to prevent regression to the old form-only layout.
- Updated the project-wide audit wording to mark PartyEditorTab as refactored and leave Voucher/Expense as the next shell targets.

## Validation

Executed:

```bash
python tools/phase220_party_document_shell_guard.py
python tools/phase219_projectwide_architecture_audit.py
python tools/phase212_runtime_stabilization_guard.py
python -m compileall -q alrajhi_client alrajhi_server
```

## Remaining Work

- `VoucherEditorTab` still needs a Finance Document Shell layout.
- `ExpenseDocumentTab` still inherits the general voucher shell and should become a dedicated expense document shell.
