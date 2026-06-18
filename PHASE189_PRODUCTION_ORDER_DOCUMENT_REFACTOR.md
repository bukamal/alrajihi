# Phase 189 — Production Order Document Refactor

This phase converts the production-order creation workflow from a modal-dialog wrapper into a real workspace document tab.

## Added

- `ProductionOrderDocumentTab` now inherits `BaseDocumentTab` directly.
- `LegacyProductionOrderDocumentTab` remains available as explicit fallback.
- `ProductionRequiredMaterialsModel` and `ProductionRequiredMaterialsGrid` provide a professional read-only requirements table.
- `ProductionSummaryPanel` summarizes required, available, shortage, and insufficient material counts.
- `production_required_materials_schema()` centralizes columns.

## Behaviour

- Product selection is editable and case-insensitive.
- Required materials are calculated through `manufacturing_service.get_required_materials_recursive()`.
- Raw and output warehouses respect `settings_service.get_manufacturing_settings()` defaults.
- Creation uses `manufacturing_service.create_production_order()` only.
- Operation state respects `manufacturing_operation_policy.OP_ORDER_CREATE`.
- Remote required-material preview now passes `warehouse_id` to the API route when available.

## Not included

- Production lifecycle/details are still legacy-backed. They are planned for the next lifecycle phase.
- Manufacturing print bridge is still a later phase.
