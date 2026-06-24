# Phase 378 — Inline Runtime Hotfix

This phase fixes runtime regressions reported after the inline editor rollout.

## Scope

- User management no longer falls back to `UserDialog` when inline creation/editing fails.
- `UserDocumentTab` accepts string user IDs such as `user_...` and no longer casts user IDs to `int`.
- Receipt/payment voucher menu choices open type-specific inline editors; the voucher type selector is locked to the chosen action.
- Expense vouchers keep their dedicated `ExpenseDocumentTab` inline editor.
- Cashbox and bank-account add/edit are now inline master-detail flows inside `CashboxesWidget`; they no longer call `open_cashbox_document` / `open_bank_account_document` from the widget toolbar.
- Main menu/quick-action routes for customers, suppliers, categories, vouchers, users, branches, warehouses, cashboxes, bank accounts, and inventory transfers route to singleton list workspaces and trigger inline actions there.

## Guard

`tools/phase378_inline_runtime_hotfix_guard.py` validates the inline routing and blocks the reported regressions.
