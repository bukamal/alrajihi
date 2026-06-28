# Phase 427 — Direct QTableWidget Editable Surface Sweep

## Purpose

Phase 426 fixed Enter navigation in the central keyboard engine, but any editable table built directly as `QTableWidget` could still bypass that engine.  Phase 427 closes that gap by sweeping direct `QTableWidget` construction and either migrating editable surfaces to `EditableSmartGrid` or proving that the direct table is read-only.

## Changes

### Restaurant simple POS invoice table

`alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py`

The restaurant simple POS invoice table was migrated from direct `QTableWidget` to `EditableSmartGrid`.

Before, this surface could edit quantity/notes outside the centralized Enter policy.

Now it uses the same `StandardTableKeyboardMixin` path as the rest of the editable grid family.  It also no longer uses `SelectedClicked` as an edit trigger, so selecting a row/cell does not open a destination editor that can serialize an empty value.

### Settings column contract surface

`alrajhi_client/views/widgets/settings_widget.py`

The settings column-contract table was migrated to `EditableSmartGrid` and explicitly set to `NoEditTriggers`, because its interaction is through embedded checkboxes rather than direct cell editing.

### Direct QTableWidget audit

Added a project-level sweep contract:

`alrajhi_client/workspace/quality/direct_qtablewidget_editable_sweep_contract.py`

Added guard:

`tools/phase427_direct_qtablewidget_editable_sweep_guard.py`

Allowed direct `QTableWidget` construction remains only for classified read-only display surfaces, currently:

- `apparel_workspace_widget.report_table`
- `apparel_workspace_widget.matrix_table`

Both are guarded as read-only via `NoEditTriggers`.

## Rule after Phase 427

Editable production surfaces must use:

- `EditableSmartGrid`, or
- another class that explicitly inherits `StandardTableKeyboardMixin`.

Direct `QTableWidget` is allowed only when it is proven read-only and classified in the Phase 427 contract.

## Verification

- `compileall`
- Phase 414–427 guards
- Phase 427 tests
- Release/packaging guards

## Remaining runtime note

This phase closes the static/direct-surface gap.  The final proof is still runtime: run the Phase 416 harness on the real PyQt environment and test Enter in every operational screen.
