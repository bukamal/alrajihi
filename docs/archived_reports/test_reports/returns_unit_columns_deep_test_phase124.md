# Phase124 — Returns Unit Columns Deep Test

## Scope
Tested the arithmetic linkage between return-line columns in both sales returns and purchase returns:

- original purchased/sold quantity
- previous returned quantity
- returnable quantity
- return quantity input
- selected unit
- displayed unit price
- line total
- base quantity saved to inventory/accounting paths

## Core invariant
All operational validation is now based on base quantity:

`base_return_qty = displayed_return_qty × selected_unit_conversion_factor`

All displayed quantities are projections from the same base quantities:

`display_qty_for_selected_unit = base_qty / selected_unit_conversion_factor`

The return price is never trusted from the UI. It is derived from the original invoice line:

`selected_unit_price = original_invoice_unit_price / original_invoice_unit_factor × selected_unit_factor`

## Tested scenario
Item: Sugar

- Base price: 5,000
- Bag factor: 10
- Sack factor: 50
- Original purchase/sale invoice: 10 sacks
- Original invoice unit price: 250,000
- Original base quantity: 500
- Previously returned: 1 sack = 50 base units

Expected results:

| Selected unit | Purchased/Sold | Previous returned | Returnable | Unit price | Return qty | Saved base qty | Line total |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sack factor 50 | 10 | 1 | 9 | 250,000 | 2 | 100 | 500,000 |
| Bag factor 10 | 50 | 5 | 45 | 50,000 | 12 | 120 | 600,000 |
| Base unit factor 1 | 500 | 50 | 450 | 5,000 | 120 | 120 | 600,000 |

Over-return guard verified:

- Returning 10 sacks after 1 sack was already returned is rejected because available is 9 sacks.

## Fixes applied

1. Return table now recalculates original quantity, previously returned, and returnable quantity according to the currently selected unit.
2. Return quantity input is validated against returnable base quantity.
3. Unit price is recalculated from the original invoice base-unit price and the selected unit factor.
4. Local sales/purchase return gateways no longer trust client-supplied `unit_price` or `conversion_factor`; they resolve the selected unit from `item_units` / item base unit.
5. Return line schema now supports `unit_id` and `conversion_factor` for sales and purchase return lines.
6. Runtime schema guard now creates `inventory_ledger` and the required indexes, preventing old local databases from failing with `no such table: inventory_ledger`.
7. Server-side return creation uses the same unit/price validation logic.

## Tests run

- `python -m compileall -q alrajhi_client alrajhi_server`
- `python tools/returns_unit_columns_deep_test_phase124.py`
- `python tools/phase32_invoice_flow_guard.py`
- `python tools/invoice_units_guard.py`
- `python tools/verify_language_phase78_sales_purchases_returns.py`
- `python tools/phase118_no_top_info_cards_guard.py`

Result: PASS.
