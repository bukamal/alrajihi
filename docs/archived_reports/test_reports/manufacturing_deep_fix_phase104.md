# Phase 104 - Manufacturing deep regression fixes

## Scope
Targeted fixes after the deeper manufacturing test reported:
1. `get_required_materials` returned only direct BOM lines and did not recursively explode multi-level BOMs.
2. A BOM line could store a `unit_id` belonging to another item, causing the wrong `conversion_factor` to be applied.

## Changed files
- `alrajhi_client/database/dao/manufacturing_dao.py`
- `alrajhi_server/api/manufacturing.py`
- `tools/manufacturing_deep_regression_test.py`

## Fixes

### 1. Unit ownership validation
BOM validation now rejects any `unit_id` unless it exists in `item_units` for the same `item_id` used by the BOM line.

Validation query:

```sql
SELECT id FROM item_units WHERE id=? AND item_id=?
```

This prevents applying a `conversion_factor` from an unrelated item.

### 2. Safer unit joins
BOM reads now join units with both `unit_id` and `item_id`:

```sql
LEFT JOIN item_units u ON bl.unit_id = u.id AND u.item_id = bl.item_id
```

This prevents stale or mismatched unit rows from leaking into BOM calculations.

### 3. Recursive material requirements
The local `get_required_materials(bom_id, planned_qty)` now delegates to the same recursive expansion used by production orders and availability checks.

This unifies these paths:
- BOM material preview
- availability check
- production order reservation
- production consumption/costing

## Regression scenario

### Invalid unit ownership
- Raw A has unit `box = 12 pcs`.
- Raw B has unit `pallet = 100 pcs`.
- Attempted BOM line: Raw A with Raw B's `pallet` unit.
- Result: rejected.

### Multi-level BOM
Subassembly BOM:
- 1 box Raw A produces 2 subassemblies.

Final BOM:
- 1 subassembly + 0.5 Raw B produces 1 final item.

Planned production:
- 4 final items.

Expected:
- Raw A: `1 * 12 * (4 / 2) = 24 pcs`.
- Raw B: `0.5 * 4 = 2 pcs`.
- Total cost: `24*2 + 2*5 = 58`.
- Final unit cost: `58 / 4 = 14.5`.

Actual:
- Raw A required/reserved: `24`.
- Raw B required/reserved: `2.0`.
- Final unit cost: `14.5`.
- After completion: Raw A `76`, Raw B `98`, Final `4`.

## Executed tests

```text
python3 -m compileall -q alrajhi_client alrajhi_server tools
python3 tools/manufacturing_flow_guard.py
python3 tools/manufacturing_numeric_guard.py
python3 tools/manufacturing_runtime_flow_test.py
python3 tools/manufacturing_units_runtime_test.py
python3 tools/manufacturing_deep_regression_test.py
```

All passed.

## Status
PASS
