# Phase 195 — Inventory / Warehouse Workspace Professionalization

This phase upgrades the warehouse and inventory workspace after Phase 194 introduced inventory governance.

## Scope

- Professionalized `WarehousesWidget` without bypassing `WarehouseService`, `InventoryService`, or `inventory_operation_policy`.
- Added a stable inventory workspace schema in `features/inventory/inventory_workspace_schema.py`.
- Added translated column keys and practical table presets for:
  - Warehouses
  - Item balances
  - Stock movements
  - Warehouse transfers
- Added row-density controls: compact / comfortable / touch.
- Added filters:
  - Balance stock status: all / positive / zero / negative
  - Movement type: purchase / sale / transfer / manufacturing / adjustment
  - Transfer status: all / active / cancelled
  - Movement and transfer search fields
- Preserved SmartTableView column chooser, reorder, filters, sorting, and per-user layout behavior.
- Fixed source-row-safe selection for warehouse and transfer actions under sorting/filtering.

## Important guardrail

`current_warehouse_id()` and `current_transfer_id()` no longer use `idx.row()` directly. They map through `SmartTableView.current_source_row()` so edit/archive/cancel actions do not target the wrong row after sorting or filtering.

## Files added

- `alrajhi_client/features/inventory/__init__.py`
- `alrajhi_client/features/inventory/inventory_workspace_schema.py`
- `tools/phase195_inventory_workspace_guard.py`

## Files changed

- `alrajhi_client/views/widgets/warehouses_widget.py`
- `alrajhi_client/i18n/translator.py`

## Validation

Executed:

```bash
python tools/phase194_inventory_governance_guard.py
python tools/phase193_manufacturing_workspace_guard.py
python tools/phase195_inventory_workspace_guard.py
python -m compileall -q alrajhi_client alrajhi_server
```

All passed.
