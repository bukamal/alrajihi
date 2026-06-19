# Phase 223 — Finance List Legacy Cleanup

## Scope

This phase removes large embedded modal editor fallbacks from finance listing widgets after the document-shell migration.

## Changes

- `VouchersWidget` no longer contains or instantiates `VoucherDialog`.
- Voucher create/edit routes exclusively through `MainWindow.open_quick_voucher()`.
- Expense rows still route through `open_quick_voucher(..., type='expense')`, which delegates to `open_expense_document()`.
- Voucher list amount display now uses `currency.format_base_amount(...)` instead of a hardcoded `USD -> display` conversion.
- `CashboxesWidget` no longer contains or instantiates `CashboxDialog` or `BankDialog`.
- Cashbox create/edit routes through `MainWindow.open_cashbox_document()`.
- Bank account create/edit routes through `MainWindow.open_bank_account_document()`.
- If a widget is ever hosted outside `MainWindow`, it now reports `cannot_open_document_tab` instead of silently reverting to legacy CRUD dialogs.

## Rationale

Phases 220–222 aligned parties, vouchers, and expenses with document-shell UX. The list widgets still had legacy modal editor classes as fallback paths. Those fallbacks could reintroduce old form-stack behavior and bypass the document-tab architecture.

## Guard

Added:

```bash
python tools/phase223_finance_list_legacy_cleanup_guard.py
```

The guard prevents `VoucherDialog`, `CashboxDialog`, `BankDialog`, direct `QDialog` editor fallback, and direct `.exec()` usage from returning to the affected finance list widgets.
