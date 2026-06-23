# Phase 343 — Runtime Application Sweep

This phase expands the unified table-column contract from the first high-risk
screens into the older list, report and operational tables.

## Scope

- Adds column contracts for remaining registered workspace tables.
- Adds stable identity-to-contract aliases for legacy `SmartTableView` screens.
- Auto-binds contracts from `CustomTableView.set_table_identity()`.
- Adds runtime identities for cashbox/bank/shift/movement tables, branches, and
  the general reports tables.
- Adds a PyQt-free sweep contract and release guard.

## Contract

Every registered workspace table in `PAGE_MANIFESTS` must resolve to a
`TableColumnContract`, and every identity alias in `TABLE_IDENTITY_CONTRACTS`
must resolve to an existing contract.

This keeps display, print and export column preferences available across:
materials, categories, parties, warehouses, cashboxes, users, audit logs,
vouchers, invoice lists, return lists, reports, manufacturing lists, restaurant,
cafe, POS, apparel and barcode multi-print.
