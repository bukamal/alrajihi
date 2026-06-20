# Phase 269 — Manufacturing Print / Currency Unification

## Scope

This phase fixes manufacturing presentation and print defects observed in BOM / production-order screens and browser HTML print output.

The target issues were:

- Manufacturing printouts exposed raw Decimal/scientific values such as `0E+1` and `1E-22-`.
- Manufacturing cost fields were shown as plain numbers instead of the configured display currency.
- BOM and production-order print templates mixed money, quantity, percent, and count values without a consistent formatting policy.
- Manufacturing UI summary panels and grids did not use the unified `MoneyDisplayPolicy` introduced for invoices, POS, returns, and reports.

## Changes

### Printing templates

Updated `alrajhi_client/printing/print_templates.py`:

- Added manufacturing-specific helpers:
  - `_manufacturing_currency(...)`
  - `_mfg_money(...)`
  - `_mfg_qty(...)`
  - `_mfg_percent(...)`
  - `_mfg_int(...)`
- Updated:
  - `manufacturing_bom_html(...)`
  - `production_order_html(...)`
  - `manufacturing_pick_ticket_html(...)`
  - `manufacturing_cost_report_html(...)`
- Cost values now pass through `_format_money(...)` and respect the display/document currency.
- Quantity values now pass through `_format_quantity(...)`.
- Waste percentages are formatted as percentages.
- Counts are formatted as integer-like values.

### Manufacturing print bridge

Updated `alrajhi_client/features/manufacturing/manufacturing_printing_bridge.py`:

- Added `_money_context()` and `_display_currency()`.
- BOM and production-order payloads now include:
  - `display_currency`
  - `currency`
  - `currency_code`

This gives the print layer explicit manufacturing currency context and avoids accidental fallback to stale or wrong labels.

### Manufacturing UI

Updated manufacturing UI components to use `core.money_display_policy`:

- `BomSummaryPanel`
- `BomComponentsModel`
- `ProductionSummaryPanel`
- `ProductionLifecycleSummaryPanel`
- `ProductionRequiredMaterialsModel`
- `ProductionLifecycleTableModel`

Money fields such as `unit_cost`, `total_cost`, `material_cost`, `waste_cost`, and lifecycle costs now display with the configured currency symbol. Quantity fields remain quantity-only and do not receive currency symbols.

## Compatibility

No database migration is required.

The phase does not alter manufacturing business calculations or exchange-rate conversion logic. It only fixes the display/print formatting boundary and passes explicit currency metadata to manufacturing print payloads.

## Verification

Added:

`tests/test_phase269_manufacturing_print_currency_unification.py`

The tests assert that:

- Manufacturing templates compile.
- BOM print output does not contain `0E+1` or `1E-22-`.
- Production-order and cost-report print output format costs as display-currency money.
- Manufacturing UI models/panels delegate to `MoneyDisplayPolicy`.
- The manufacturing print bridge passes explicit currency context.
