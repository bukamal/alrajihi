# Phase 52 — Manufacturing Document Tabs

## Scope
Converted manufacturing workflows from modal-only navigation into workspace document tabs while keeping the existing manufacturing service/gateway boundaries intact.

## Implemented
- Added `features/manufacturing/BomDocumentTab`.
- Added `features/manufacturing/ProductionOrderDocumentTab`.
- Added `features/manufacturing/ProductionOrderDetailsTab`.
- Added `MainWindow.open_bom_document()`.
- Added `MainWindow.open_production_order_document()`.
- Added `MainWindow.open_production_order_details()`.
- Routed `ManufacturingWidget` add/edit/view actions to workspace tabs.
- Preserved BOM component `unit_id` so material unit conversions remain active in manufacturing.
- Added `tools/document_tabs_phase52_guard.py`.

## Architecture
The new document tabs are workspace containers. They do not access SQL, DAO, or repositories directly. Persistence remains behind `manufacturing_service` and existing gateways.

## Verification
- `python tools/architecture_guard.py`
- `python tools/document_tabs_guard.py`
- `python tools/document_tabs_phase47_guard.py`
- `python tools/document_tabs_phase48_guard.py`
- `python tools/document_tabs_phase49_guard.py`
- `python tools/document_tabs_phase50_guard.py`
- `python tools/document_tabs_phase51_guard.py`
- `python tools/document_tabs_phase52_guard.py`
- `python tools/unified_printing_guard.py`
- `python tools/smart_table_rollout_guard.py`
- `pytest -q` → 84 passed, 1 pre-existing warning
- `python -m compileall -q alrajhi_client alrajhi_server tools tests`
