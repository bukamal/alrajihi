# Phase 51 — Voucher Document Tabs

## Scope
Converted receipt, payment, and expense vouchers from the temporary `DialogDocumentTab` bridge into a real workspace document tab.

## Implemented
- `VoucherEditorTab(BaseDocumentTab)`.
- `VoucherHeaderPanel` for type/date/description/reference.
- `VoucherLinkPanel` for customer/supplier and unpaid invoice linkage.
- `VoucherPaymentPanel` for amount, cashbox, bank account, and currency conversion.
- `VoucherActionsPanel` for local save/print actions mirroring `UnifiedActionBar`.
- Save/update through `voucher_service` only.
- Preview/export through the unified `printing_service` voucher pipeline.
- Dirty state is raised by panel edits and cleared after successful save.

## Preserved boundaries
- No direct SQL in voucher UI.
- No `DatabaseConnection` in voucher UI.
- No local printing bypass; voucher print/export remains unified.
- Existing voucher list still routes add/edit to workspace tabs.

## Verification
- `tools/document_tabs_phase51_guard.py`
- `pytest`
- `compileall`
