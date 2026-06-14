# GATEWAY PHASE 79 — Inventory / Items / Warehouses Localization

## Scope
- Items list (`items_widget.py`)
- Item dialog (`item_dialog.py`)
- Warehouses, balances, movements, and transfers (`warehouses_widget.py`)

## Language policy
- Arabic remains the source/default language and uses RTL.
- German is the second UI language and uses LTR.
- English is the third UI language and uses LTR.

## Changes
- Added Arabic/German/English translation keys for inventory, item, stock, warehouse, balance, movement, transfer, and unit conversion UI terms.
- Converted visible labels, buttons, table headers, placeholders, titles, and key toast messages in the scoped files to `translate(...)`.
- Preserved internal canonical Arabic item type values (`مخزون`, `منتج نهائي`, `خدمة`) via `QComboBox` item data, so backend filtering/saving remains compatible while display text changes by language.
- Applied `qt_layout_direction()` to item and warehouse screens/dialogs.
- Added `tools/verify_language_phase79_inventory_items.py` guard.

## Validation
- `python tools/verify_language_phase79_inventory_items.py` ✅
- `python -m compileall -q alrajhi_client tools` ✅

## Notes
This phase does not convert manufacturing, finance, reports, or full print templates. Those should remain separate phases to avoid high-risk broad changes.
