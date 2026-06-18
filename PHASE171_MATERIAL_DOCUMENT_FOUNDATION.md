# Phase 171 — Material Document Foundation

## Purpose

Phase 171 moves the material editor away from the old modal-dialog model and aligns it with the tabbed ERP document direction used by the new transaction screens.

The goal is not to create a separate barcode or unit system.  The material tab now uses the project's existing services and settings contracts:

- `product_service`
- `barcode_service`
- `barcode_input_service`
- `barcode_label_service`
- `settings_service`
- `printing_service`
- local/remote product gateways
- `i18n` Arabic / German / English translations

## Main changes

### MaterialDocumentTab

`alrajhi_client/features/items/item_editor_tab.py` now exposes:

- `MaterialDocumentTab`
- backward-compatible alias `ItemEditorTab = MaterialDocumentTab`

The new tab includes:

- header actions
- material/basic-data panel
- pricing and inventory panel
- barcode and label panel
- units grid with a unit-barcode column
- bottom action bar
- `Ctrl+S` save
- `Ctrl+P` print label
- `Ctrl+B` generate barcode
- `Ctrl+Shift+B` scan with camera

### Barcode support

The material tab now preserves the barcode capabilities that previously existed only in `ItemDialog`:

- generate EAN13
- generate CODE128
- validate barcode using `barcode_service`
- normalize camera/scanner input using `barcode_input_service`
- scan using `BarcodeCameraDialog`
- print/preview labels using `barcode_label_service` and `printing_service`

Barcode defaults are now read from `settings_service.get_material_settings()` instead of being hardcoded in the tab.

### Settings contract

Added:

```python
settings_service.get_material_settings()
```

The contract includes:

- default barcode symbology
- EAN13 internal prefix
- CODE128 prefix
- auto-generate barcode policy
- barcode-required policy for stock items
- manual barcode edit policy
- default unit
- default item type
- quantity/price decimals
- barcode label options inherited from printing settings

### Units

The units grid now has a forward-compatible schema:

- Unit
- Conversion Factor
- Unit Barcode
- Notes

The current local persistence still saves the legacy unit fields.  Unit-barcode persistence and barcode lookup by unit are intentionally left for the next API/database phase.

### Workspace alignment

The dashboard add-material shortcut no longer opens the legacy modal `ItemDialog`; it routes to `MainWindow.open_item_document()` when available.

The old `ItemDialog` remains as legacy fallback only.

## Validation

Executed successfully:

```bash
python tools/phase169_system_governance_guard.py
python tools/phase170_barcode_api_guard.py
python tools/phase171_material_document_guard.py
python -m compileall -q alrajhi_client alrajhi_server
```

## Next recommended phase

Phase 172 should implement real unit-barcode persistence and lookup:

- add `barcode` / `unit_barcode` fields to item units in local DB and server DB
- include unit barcodes in item create/update API
- extend `/api/items/by-barcode` to return matched base item or matched unit
- update `product_service.item_by_barcode()` or add `product_service.resolve_barcode()`
- update POS and transaction scan flows to respect matched unit and conversion factor
