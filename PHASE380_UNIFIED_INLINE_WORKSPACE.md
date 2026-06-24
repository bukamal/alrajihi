# Phase 380 — Unified Inline Workspace Contract

This phase consolidates the inline editor shell used by list/detail workspaces.

## Implemented

- Added `UnifiedInlineWorkspaceMixin` as the common inline master-detail host.
- Converted the generic document inline host to delegate to the unified shell.
- Converted the customer/supplier party inline host to delegate to the unified shell.
- Converted vouchers to use the same unified shell instead of duplicating local stack/splitter boilerplate.
- Standardized the outer inline toolbar to a minimal back-only row.
- Removed duplicate outer inline title labels from document/party/voucher inline shells.
- Fixed `ResponsiveMasterDetail.set_initial_sizes()` so it respects `master_weight` and `detail_weight`; wide detail panes now actually receive the larger horizontal share.
- Widened cashbox and bank inline panes and removed their visible outer inline title label.

## Design rule

Inline editors are classified by function, but their outer container is unified:

1. Master data forms: customers, suppliers, users, categories, branches, warehouses, cashboxes and bank accounts.
2. Finance documents: receipt vouchers, payment vouchers and expense vouchers.
3. Future document grids: inventory transfers, invoices and manufacturing documents can be migrated to the same shell without adding another bespoke host.

List-local Add/Edit actions must stay in the current workspace and must not spawn sub-tabs.
