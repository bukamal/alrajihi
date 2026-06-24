# Phase 375 — Inline Party and Voucher Editors

## Goal

Customer, supplier and voucher list pages should not spawn additional workspace tabs when the user presses Add or opens a record from that same list. The interaction remains inside the current tab as a professional inline master-detail/editor workflow.

## Scope

- Customers list: Add/Edit opens `PartyEditorTab` inline in the detail pane.
- Suppliers list: Add/Edit opens `PartyEditorTab` inline in the detail pane.
- Vouchers list: Add opens an inline editor for:
  - سند قبض / receipt voucher
  - سند دفع / payment voucher
  - سند مصروف / expense voucher
- Voucher edit opens the selected record inline; expense records use `ExpenseDocumentTab`.

## Non-goals

Global shortcuts and dashboard actions may still open full document tabs. Phase 375 only changes list-local Add/Edit behavior.

## Runtime policy

- Inline editors use `QStackedWidget` to switch between preview/list and editor surfaces.
- Save refreshes the source list and returns to the list surface.
- Back/Cancel uses the document `can_close()` dirty-state confirmation.
- Legacy `AddEntityDialog` remains only as a fallback if the inline editor cannot be constructed.

## Validation

- `tools/phase375_inline_party_voucher_editor_guard.py`
- `tests/test_phase375_inline_party_voucher_editor.py`
