# Phase123 Returns Unit/Ledger Fix

## Scope
- Sales returns dialog
- Purchase returns dialog
- Returnable invoice line loading
- Unit-aware return quantity and pricing
- Inventory ledger table creation for existing databases

## Fixed
1. Return item column no longer depends only on `description`; it resolves `item_name` from invoice lines and falls back to `product_service.item_by_id(item_id)`.
2. Added a selectable Unit column in sales and purchase returns.
3. Return quantity is entered in the selected unit. `quantity_in_base = return_qty * selected_conversion_factor`.
4. Price is recalculated from the original invoice base-unit price:
   `selected_unit_price = original_unit_price / original_factor * selected_factor`.
5. Previous returned, returnable, and original quantity display are recalculated for the selected unit.
6. Refund amount entered in display currency is converted back to USD/internal currency before saving.
7. Existing databases without `inventory_ledger` are healed by `CREATE TABLE IF NOT EXISTS inventory_ledger` before ledger posting.
8. Server return endpoints now accept selected unit/price/factor and create `inventory_ledger` if missing.

## Example
If base price is 5,000 SYP and:
- Kيس = 10 base units
- شوال = 50 base units

Then:
- price per Kيس = 50,000 SYP
- price per شوال = 250,000 SYP
- returning 10 شوال = 500 base units and total = 2,500,000 SYP

## Validation
- Python compileall passed for client and server.
