# Phase 441 — Semantic Visual State Migration

## Objective

Reduce high-impact hard-coded local status styles by moving material-editor status labels and frames to a centralized semantic visual-state system.

This phase is intentionally targeted. It does not remove every local `setStyleSheet()` in the project; it establishes a safe migration path and applies it to the material surfaces where red/green/orange hard-coded status labels were heavily concentrated.

## Added

- `alrajhi_client/ui/visual_state.py`
- `alrajhi_client/workspace/quality/semantic_visual_state_migration_contract.py`
- `tools/phase441_semantic_visual_state_migration_guard.py`
- `tests/test_phase441_semantic_visual_state_migration.py`

## Changed

- `alrajhi_client/features/items/item_editor_tab.py`
- `alrajhi_client/views/dialogs/item_dialog.py`
- `alrajhi_client/theme/brand.py`
- `alrajhi_client/theme/qss.py`

## Migration rule

Instead of local hard-coded styles such as:

```python
label.setStyleSheet("color: #b91c1c; font-weight: 700;")
```

use:

```python
set_visual_state(label, "danger", weight="strong", size="caption", role="semantic_status")
```

The central QSS now owns how `success`, `warning`, `danger`, `muted`, and `info` states are rendered.

## Audit effect

The legacy visual-style audit was regenerated. Local style records were reduced and hard-coded status colors were removed from the migrated material surfaces.

## Scope boundary

No business logic, pricing logic, barcode logic, stock logic, saving logic, printing, or permissions were changed.
