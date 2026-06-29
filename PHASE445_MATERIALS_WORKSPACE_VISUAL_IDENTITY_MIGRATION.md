# Phase 445 — Materials Workspace Visual Identity Migration

This phase migrates the materials workspace and material editor toward the
central Al Rajhi visual identity without changing business behavior.

## Scope

- Materials list surface.
- Materials filter row.
- Materials table header identity.
- Material document/editor cards.
- Material units table and bottom action bar.
- Runtime visual polish preservation for explicit material roles.

## What changed

- Added Phase445 material design tokens in `theme/brand.py`.
- Added centralized QSS selectors for:
  - `MaterialsFilterCard`
  - `materials_filter`
  - `materials_table`
  - `material_form_card`
  - `MaterialEditorActionBar`
- Wrapped material filters in a real visual card instead of a raw inserted layout.
- Marked material list toolbar/search/table with semantic visual roles.
- Marked material editor panels with explicit semantic card roles:
  - `MaterialBasicCard`
  - `MaterialPricingCard`
  - `MaterialBarcodeCard`
  - `MaterialUnitsCard`
- Removed the local `item_editor_tab.py` style block that used generic palette
  selectors and replaced it with centralized role-based styling.
- Updated runtime visual polish so it does not overwrite explicit material
  visual roles.

## Non-goals

- No change to item save/update/delete logic.
- No change to barcode generation or printing logic.
- No change to stock/cost calculations.
- No change to permissions or API behavior.

## Validation

- `tools/phase445_materials_workspace_visual_identity_guard.py`
- `tests/test_phase445_materials_workspace_visual_identity.py`
