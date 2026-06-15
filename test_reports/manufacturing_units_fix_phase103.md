# Phase 103 - Manufacturing BOM Units Fix

## Scope
Applied a targeted manufacturing accounting/stock fix for BOM component quantity calculation in both local and server paths.

## Fixed files
- `alrajhi_client/database/dao/manufacturing_dao.py`
- `alrajhi_server/api/manufacturing.py`
- Added `tools/manufacturing_units_runtime_test.py`

## Correct formula
For every BOM line, required material quantity is now calculated in the component base unit:

`required_qty = line.quantity * conversion_factor * (planned_qty / bom.quantity) * (1 + waste_percent)`

Where:
- `line.quantity`: component quantity as entered in BOM.
- `conversion_factor`: selected secondary unit conversion to the item base unit; base unit = 1.
- `planned_qty / bom.quantity`: scales the line by the BOM parent quantity.
- `waste_percent`: stored as decimal ratio; 10% = `0.10`.

## Runtime test scenario
- Raw item base unit: `pcs`.
- Secondary unit: `box = 12 pcs`.
- BOM parent quantity: `2` finished units.
- BOM component: `1 box` raw material.
- Waste: `10%`.
- Planned production: `4` finished units.
- Expected raw consumption: `1 * 12 * (4 / 2) * 1.10 = 26.4 pcs`.
- Raw cost: `2` per pc.
- Expected finished unit cost: `(26.4 * 2) / 4 = 13.2`.

## Verified results
- Required material quantity: `26.40`.
- Reservation quantity: `26.40`.
- Raw stock after completion: `73.6` from initial `100`.
- Finished stock after completion: `4`.
- Finished unit cost: `13.2`.
- Finished average cost: `13.2`.
- Raw stock after reverse: `100`.
- Finished stock after reverse: `0`.

## Tests run
- `python3 -m compileall -q .`
- `python3 tools/manufacturing_flow_guard.py`
- `python3 tools/manufacturing_numeric_guard.py`
- `python3 tools/manufacturing_runtime_flow_test.py`
- `python3 tools/manufacturing_units_runtime_test.py`
- `python3 tools/verify_language_phase80_manufacturing.py`
- Server arithmetic helper check: `26.40` PASS.

## Result
PASS. Manufacturing unit conversion, BOM quantity scaling, waste, reservation, stock movement, final product cost, and reverse production are now consistent for the tested unit-linked manufacturing path.
