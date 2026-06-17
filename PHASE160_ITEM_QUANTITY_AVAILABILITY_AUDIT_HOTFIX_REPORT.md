# Phase 160 - Item Quantity / Available Quantity Audit & Hotfix

## Scope
Audited the discrepancy between the item table columns:

- `quantity`
- `available_quantity`

especially after sales, purchases, sales returns, purchase returns, and manufacturing reversals.

## Findings

1. The item table UI displayed `quantity` from `opening_quantity`, while `available_quantity` was calculated from inventory movements.
   - This made the two columns diverge by design after any real stock movement.
   - It confused users because `quantity` looked like current stock but was actually opening stock.

2. Some stock aggregation queries did not include all stock movement types consistently.
   - `purchase_return` was missing from some negative stock calculations.
   - `sales_return` and `consumption_reverse` were missing from some positive stock calculations.
   - This could cause divergence between `items.quantity` and calculated `available` after returns/manufacturing reversals.

## Implemented Fix

### UI definition fixed

`ItemsWidget.prepare_table_data()` now treats:

- `quantity` = current stock balance from `items.quantity`
- `available_quantity` = calculated available stock from inventory movements

Since no reservation system is currently active, both values should normally match.

Opening quantity remains available in the item edit dialog as `opening_quantity`, not as the main table `quantity` column.

### Stock formula normalized

The stock movement formula was normalized in client/server stock queries:

Positive movements:

- `opening`
- `purchase`
- `adjustment`
- `production_out`
- `sales_return`
- `consumption_reverse`

Negative movements:

- `sale`
- `production_consume`
- `purchase_return`

Affected areas include:

- `alrajhi_client/database/connection.py`
- `alrajhi_client/database/dao/inventory_movement_dao.py`
- `alrajhi_server/api/items.py`
- `alrajhi_server/api/invoices.py`
- `alrajhi_server/api/returns.py`
- related manufacturing stock calculations

## Tests

Passed:

- Python compile check: `python3 -m compileall -q alrajhi_client alrajhi_server tools`
- Architecture guard: `python3 tools/architecture_guard.py`
- Inventory formula test:
  - opening +10
  - purchase +5
  - sale -3
  - sales return +1
  - purchase return -2
  - production consume -4
  - consumption reverse +1
  - production out +7
  - expected balance: 15
  - actual balance: 15

## Expected Behavior After Fix

For normal items without reservations:

- `quantity` and `available_quantity` should match.
- Purchases increase both.
- Sales decrease both.
- Sales returns increase both.
- Purchase returns decrease both.
- Manufacturing consumption decreases both.
- Production output increases both.

If a reservation system is added later, `available_quantity` may become:

`quantity - reserved_quantity`

but that is not active in the current project.
