# Phase 275 — Reports Calculation / Currency / Table UX Consolidation

## Scope

This phase fixes the reports workspace before continuing the general unification roadmap.

The user-reported problems were:

- report tabs are too many and difficult to navigate;
- several report tables display money/cost fields inconsistently;
- some report totals do not visibly calculate in the summary bar;
- report tables are not consistently optimized for dense accounting data.

## Changes

### 1. Grouped report navigation

`ReportsWidget` now groups report tabs into high-level families instead of placing every report at the top level:

- `reports_group_financial`
- `reports_group_parties`
- `reports_group_inventory`
- `reports_group_cash_pos`
- `reports_group_profit_manufacturing`
- `reports_group_diagnostics`

The concrete report tabs still exist and keep their original widgets, tables, Report Shell metadata, API resources, permissions, printing, export, branch scope, and audit bindings.

### 2. Active report resolution

The widget now resolves the active concrete report using:

- `_active_report_tab()`
- `_active_report_title()`
- `_report_table_for_tab(tab)`

This keeps refresh and printing correct after grouping.

### 3. Unified report money and quantity helpers

`ReportsWidget` now has display helpers:

- `_money(value, display_curr)` — converts persisted/storage amounts to display currency and formats them through the unified currency policy.
- `_qty(value)` — formats report quantities without currency symbols.
- `_money_sum(...)` — sums raw storage amounts and formats them in display currency.

This specifically fixes report cells that previously formatted storage/base amounts directly as display currency.

### 4. Fixed report table currency spots

The following reports were updated to use report display helpers:

- warehouse balances average cost and stock value;
- warehouse movements unit cost;
- warehouse valuation quantities;
- warehouse transfers quantities;
- POS shift opening/cash/card/expected/actual/difference amounts.

### 5. Visible calculation summaries

Income statement and balance sheet now set summary text after refresh, showing calculated totals using the display currency.

### 6. Compact table UX

Report tables now apply a compact accounting table profile through `_apply_report_table_profile`, including compact density and report metadata properties.

## Validation

- `compileall`: passed.
- full test suite: `261 passed`, `1 warning`, `0 failed` before adding the Phase 275 guard.

