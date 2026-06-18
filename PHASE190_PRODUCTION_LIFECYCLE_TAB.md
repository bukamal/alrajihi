# Phase 190 — Production Order Lifecycle Tab

## Goal
Move production-order lifecycle details out of the legacy `ProductionDetailsDialog` wrapper and into a real workspace tab while preserving the old dialog as an explicit emergency fallback.

## Implemented

- Added `features/manufacturing/production_order_lifecycle_tab.py`.
- Exported the new `ProductionOrderDetailsTab` from `features/manufacturing/__init__.py`.
- Kept `LegacyProductionOrderDetailsTab` as a fallback wrapper around `ProductionDetailsDialog`.
- Added lifecycle schemas:
  - `production_reservations_schema()`
  - `production_consumptions_schema()`
  - `production_outputs_schema()`
- Added lifecycle model/grid:
  - `ProductionLifecycleTableModel`
  - `ProductionLifecycleGrid`
- Added `ProductionLifecycleSummaryPanel`.
- Lifecycle tab now displays:
  - Reservations / remaining materials
  - Consumptions
  - Outputs
  - Summary totals
- Lifecycle operations now execute from the tab through `ManufacturingService` and therefore through `manufacturing_operation_policy`:
  - Start production
  - Cancel order
  - Consume materials
  - Complete production
  - Reverse production
  - Delete consumption
  - Delete output
  - Print preview through centralized `printing_service.production_preview`

## Governance

The new tab does not call DAO/REST/QSettings directly. It uses:

- `manufacturing_service`
- `manufacturing_operation_policy`
- `printing_service`
- `translate()`

## Validation

Executed successfully:

```bash
python tools/phase184_case_insensitive_material_lookup_guard.py
python tools/phase185_invoice_grid_item_lookup_guard.py
python tools/phase186_pos_returns_lookup_audit_guard.py
python tools/phase187_manufacturing_governance_guard.py
python tools/phase188_bom_document_refactor_guard.py
python tools/phase189_production_order_document_refactor_guard.py
python tools/phase190_production_lifecycle_tab_guard.py
python -m compileall -q alrajhi_client alrajhi_server
```

## Next logical phase

Phase 191 — Manufacturing API / Unit Alignment:

- Make BOM lines, reservations, consumptions, and outputs consistently carry `unit_id`, `conversion_factor`, and `base_qty` through local DB and API.
- Ensure consumption and output operations store/use base quantities correctly.
- Add guards against unit-loss in manufacturing workflows.
