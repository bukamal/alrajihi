# Phase458 Contract Reconciliation & Settings/Network Integration Report

## Scope

Patched the uploaded runtime visual regression gate project to reconcile stale contracts with the newer registry/settings/network architecture, while preserving the modern lazy-loading, responsive dashboard, unified inline editors, and runtime visual gates.

## Main fixes

1. REST idempotency / offline replay safety
   - Updated `alrajhi_client/database/connection_rest.py` so request metadata headers are merged through `_headers(...)` instead of passing `extra_headers=extra_headers` as an unsafe kwarg.
   - Keeps the Phase270/420 idempotency contract intact.

2. Settings integration
   - Added `transactions/enabled` to the settings contract and the Settings > Contracts surface.
   - Transaction pages using the shared `transactions/enabled` feature flag are now represented in the UI settings surface.

3. Network runtime reset
   - Added `DatabaseConnection.reset_runtime_connection()`.
   - Settings network save now clears settings cache and resets the runtime connection when the network mode changes.

4. Restaurant/simple POS table contracts
   - Added missing table column contracts for:
     - `restaurant.simple_invoice_lines`
     - `restaurant.menu_categories`
     - `restaurant.menu_items`
   - Added compatibility aliases for restaurant/cafe table identities.

5. i18n key reconciliation
   - Added a Phase458 translation reconciliation wrapper for newly introduced navigation/barcode/workspace/settings keys across Arabic, English, German, and French.

6. Dashboard/action-bar/visual contract reconciliation
   - Removed stale fixed HBox dashboard markers that conflicted with the responsive Phase439 dashboard.
   - Reconciled the Dashboard action policy: core Dashboard actions remain `refresh`, `theme`, `screenshot`, and `user`; fullscreen remains available as an operational action where appropriate.
   - Updated stale tests/contracts to assert current responsive-grid behavior instead of old fixed `row.addWidget(..., stretch)` patterns.

7. Lazy loading and workspace routing
   - Preserved lazy page factories and removed stale eager-import expectations.
   - Updated older tests to recognize the current inline editor architecture for categories, customers, suppliers, and vouchers.
   - Transaction invoice/return routing now remains aligned with the unified transaction shell rather than legacy dialog-backed editors.

8. Login, QSS, shell identity, and keyboard contracts
   - Reconciled stale literal-marker tests with the current brand-token-driven login layout.
   - Removed forbidden legacy QSS/main-nav markers.
   - Reconciled keyboard policy tests with current non-destructive editing behavior.

## Verification performed

Static compilation:

- `python3 -m compileall -q alrajhi_client alrajhi_server tests`
- Result: `COMPILE_OK`

Targeted verification:

- Phase270/273/286/343/394/420/421: `34 passed`
- Phase422/423/424: `16 passed`
- Phase425 through Phase442 grouped verification: `102 passed`
- Phase443 through Phase457 grouped verification: `60 passed`
- Modified/stale-contract reconciliation tests: `72 passed`
- Late document/master-detail chunk 225-250: `77 passed`
- Final late chunk 250-256: `13 passed`
- Phase328-349 subgroups after reconciliation:
  - group 0: `19 passed`
  - group 5: `25 passed`
  - group 10: `21 passed`
  - group 15: `22 passed`
  - group 20: `24 passed`

A single full-suite `pytest -q tests --tb=short --maxfail=1` run was attempted. It progressed without visible failures but exceeded the execution timeout in this environment before completion. Therefore, the reliable gate for this patch is the chunked/static/targeted verification above, not a completed single full-suite run.

## Environment caveat

The GUI was not launched interactively in this environment. The available validation was static, contract-based, pytest-based, and guard-based. Runtime GUI acceptance on Windows/X11 should still be performed on the target machine.

## Remaining recommended runtime checks

1. Launch the application on the target Windows/X11 environment.
2. Switch Local/Client/Server mode from Settings and confirm the connection reset behavior.
3. Confirm Settings > Contracts now exposes Transactions.
4. Open Sales, Purchase, Returns, Restaurant, Cafe, Apparel, POS, Customers, Suppliers, Categories, and Vouchers.
5. Test Arabic/English/German/French switching, especially navigation labels and barcode profile labels.
6. Test multi-user remote mode with two clients performing invoice/save/offline-replay scenarios.

## Status

Phase458 patch is ready for manual runtime acceptance testing.
