# Phase 204 — Voucher Governance / Workspace Hardening

- Added voucher create/edit/delete/print/view operations to finance settings, RBAC, and finance operation policy.
- Routed VoucherService add/update/delete/list/get through FinanceOperationPolicy.
- Hardened VouchersWidget buttons and actions with policy checks.
- Fixed voucher table selection to use SmartTableView.current_source_row() so sorting/filtering cannot delete/print the wrong voucher.
- VoucherEditorTab now enforces create/edit/print policy and becomes read-only when saving is not allowed.
- Added voucher governance translations and guard.
