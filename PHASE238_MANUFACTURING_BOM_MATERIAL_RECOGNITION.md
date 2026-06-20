# Phase 238 — Manufacturing BOM Material Recognition Hotfix

## Problem
After adding materials to manufacturing/BOM and creating a production order, the production-order flow could still report that no production materials existed.

The root causes were:

1. Item type values were accidentally made language-dependent during UI i18n cleanup. New items could be saved as `Finished product`, `Inventory`, or German equivalents instead of canonical business values.
2. Manufacturing filters and validation only accepted exact Arabic/internal values such as `منتج نهائي`.
3. `ProductionOrderDocumentTab` trusted the initial BOM cache. If the tab was already open while a BOM was created/edited, it continued saying no BOM/materials existed.
4. `manufacturing_dao.get_bom()` referenced `bl.unit_name`, but the local `bom_lines` table does not contain that column.
5. `ManufacturingService.get_required_materials_recursive()` did not normalize string quantities to `Decimal` at the service boundary.

## Fixes

- Added `alrajhi_client/core/item_types.py` with canonical item-type constants and legacy localized alias normalization.
- Material add/edit dialogs now store canonical business values:
  - `مخزون`
  - `منتج نهائي`
  - `خدمة`
- Existing records saved with English/German item-type labels are still recognized.
- Manufacturing BOM/product filters now use `is_finished_product()` / `is_bom_component_type()` instead of raw string equality.
- Production-order required materials refresh now re-reads the latest BOM from the service instead of relying only on `_product_bom_map` cache.
- Local manufacturing DAO no longer selects non-existent `bl.unit_name`.
- Required-material quantity input is normalized to `Decimal` at the service boundary.

## Guard
Added:

```bash
python tools/phase238_manufacturing_bom_material_recognition_guard.py
```

The guard creates a local DB, inserts a finished product using the legacy English item type `Finished product`, inserts a raw material using `Inventory`, saves a BOM, calculates required materials, creates a production order, and verifies material reservations are created.

## Verification

Executed successfully:

```bash
python tools/phase238_manufacturing_bom_material_recognition_guard.py
python tools/phase237_browser_html_print_guard.py
python tools/phase236_print_settings_contract_guard.py
python tools/phase235_unified_print_button_guard.py
python tools/phase233_full_unification_guard.py
python tools/phase232_project_language_audit.py
python tools/phase234_dashboard_cashbox_runtime_guard.py
python tools/phase212_runtime_stabilization_guard.py
python tools/reports_contract_check.py
python tools/advanced_runtime_test.py
python -m compileall -q alrajhi_client alrajhi_server
```
