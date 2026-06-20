# PHASE 254 — Material Shell Unification

## Objective
Unify the material/item workspace under the same Document Shell governance used by transactions: descriptor, API/network parity, permissions, settings, i18n, currency, barcode, units and print label actions.

## Changes
- Added `features/items/material_shell_contract.py` as a data-only contract for the material document/list shell.
- Corrected `MaterialDocumentTab` to initialise `BaseDocumentTab` with `document_type="material"` instead of the legacy `item` alias.
- Bound the material document to `DocumentPermissionBinder` for save/print/barcode actions.
- Preserved and named the responsive master-detail splitter as `ItemEditorResponsiveSplitter`.
- Added diagnostic shell properties: API resource, network mode and material shell matrix.
- Bound `ItemsWidget` list actions to the same material descriptor and permission binder.
- Kept remote item units policy explicit: remote mode persists units through the item create/update payload, while local mode uses replace_units.
- Added a tri-lingual material shell badge in Arabic, English and German.

## Network/API note
The material shell is network-capable through `/api/items`, `RemoteItemGateway`, exact barcode lookup and atomic item-unit payloads. No QSettings-only business state was introduced.

## Currency note
Material prices continue to respect the display currency. Phase 252 remains the formatting authority; this phase ensures the material shell declares and exposes that policy.

## Tests
Added `tests/test_phase254_material_shell_unification.py`.
