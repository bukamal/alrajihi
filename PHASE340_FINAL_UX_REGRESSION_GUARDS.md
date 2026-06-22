# Phase 340 — Final UX Regression Guards

This phase adds a PyQt-free final UX regression guard for the unified interface rollout.

## Purpose

The guard prevents regressions across the system foundations introduced in Phases 331-339:

- UI registry and shell manifest.
- Main navigation and action-bar contract.
- Dashboard minimal action surface.
- Central design tokens and typography metrics.
- Universal table column contract.
- Separate display/print/export column settings.
- Editable table keyboard behavior.
- Unified barcode printing profiles and multi-print UI.
- Browser HTML-only barcode printing path.

## Added files

- `alrajhi_client/workspace/quality/final_ux_regression_contract.py`
- `tools/phase340_final_ux_regression_guard.py`
- `tests/test_phase340_final_ux_regression_guards.py`

## Audit outputs

Running the guard writes:

- `tools/audit_outputs/final_ux_regression_matrix.csv`
- `tools/audit_outputs/final_ux_regression_summary.json`

## Guarded invariants

- Required workspaces remain in the central registry.
- All workspace actions are declared in `ACTION_SPECS`.
- Dashboard exposes only `refresh`, `theme`, `screenshot`, and `user` actions.
- Navigation entries resolve to registered workspaces.
- Table settings are scoped under `ui/columns/<page>/<table>`.
- Required table contracts exist for invoices, POS, restaurant, cafe and apparel.
- Column keys are unique per table.
- Required columns stay visible by default.
- Printing/export contracts have default output columns.
- `CustomTableView` uses the column-output contract for print/export.
- `CustomTableView` and `EditableSmartGrid` use the unified keyboard policy.
- Required barcode profiles exist for items, apparel, restaurant and cafe.
- Barcode profiles support multi-print and Browser HTML output only.
- Every barcode profile has a candidate provider.
- `BatchPrintDialog` routes profile-aware barcode printing through `printing_service`.

## Result

This phase does not add new business UI features. It adds a durable regression gate so later visual and workflow changes cannot silently break the unified shell, table, printing, barcode, and keyboard contracts.
