# Phase 92 – Controls Localization Hotfix

## Scope
- Sales invoice toolbar buttons via shared `TableToolbar`.
- Purchase invoice toolbar buttons via shared `TableToolbar`.
- Sales/purchase returns toolbar buttons via shared `TableToolbar`.
- Items toolbar buttons and extra barcode buttons.
- Items table headers.
- Column menu/reset labels.

## Changes
- `TableToolbar` no longer contains hard-coded Arabic UI labels.
- Added translation keys:
  - `add_entity`
  - `columns`
  - `excel`
  - `print`
  - `refresh`
  - `records_count`
  - `column_number`
  - `reset_columns`
- `ItemsWidget` now refreshes display headers dynamically using current language.
- `ItemsWidget` extra buttons are now created from translated runtime labels, not import-time static labels.

## Validation
- `tools/verify_phase92_controls_localization.py`
- `python -m compileall -q alrajhi_client`
