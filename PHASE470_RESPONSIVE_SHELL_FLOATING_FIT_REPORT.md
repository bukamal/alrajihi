# Phase470 — Responsive Shell & Floating Fit Cleanup

## Scope

This phase continues from Phase469 and targets the runtime screenshots that still showed crowded list/material surfaces and floating quick-create panels that needed more predictable sizing and anchoring.

No business logic, accounting calculation, database schema, service/gateway contract, or permission model was changed.

## Changes

### 1. Responsive two-row table toolbar

Updated:

- `alrajhi_client/views/widgets/components/table_toolbar.py`

The reusable `TableToolbar` no longer places all list actions, search, filters, columns, export, print, refresh, and counter in one horizontal row. It now uses a responsive two-row shell:

- `TableToolbarActionRow`
- `TableToolbarSearchRow`

The public button attributes and signals remain unchanged, so existing widgets can still use:

- `add_btn`
- `edit_btn`
- `delete_btn`
- `export_btn`
- `print_btn`
- `refresh_btn`
- `search_edit`

This directly addresses crowded list headers such as the materials list.

### 2. Materials filter grid

Updated:

- `alrajhi_client/views/widgets/items_widget.py`

The materials filters are no longer one long `QHBoxLayout`. They now use a `QGridLayout` with `MaterialsFilterCell` wrappers.

This prevents cropped labels such as `row_density`, reduces horizontal pressure, and makes the materials list more stable on laptop-width screens.

### 3. Scrollable floating quick-create forms

Updated:

- `alrajhi_client/ui/inline_quick_create.py`

The quick-create form content is now hosted inside:

- `InlineQuickCreateFormScroll`
- `InlineQuickCreateFormHolder`

This keeps floating drawers fixed and scrollable instead of letting long forms expand or clip.

The existing `InlineQuickCreatePanel` API remains intact for compatibility, but the visual behavior remains floating/overlay-first.

### 4. Drawer anchoring below the triggering control

Updated:

- `alrajhi_client/ui/floating_quick_create.py`

Floating drawers now anchor below the triggering control where possible. They no longer default to the very top of the window, which helps avoid covering global toolbars, POS headers, and scan/search bars.

The surface remains hardened with:

- `WA_StyledBackground = True`
- `WA_TranslucentBackground = False`
- `WA_NoSystemBackground = False`
- `setWindowOpacity(1.0)`
- `setAutoFillBackground(True)`

### 5. QSS visual contracts

Updated:

- `alrajhi_client/theme/qss.py`

Added Phase470 styling for:

- `QWidget[responsiveToolbarPhase="470"]`
- `QFrame#MaterialsFilterCard[materialsFilterGridPhase="470"]`
- `QFrame#MaterialsFilterCell[materialsFilterCellPhase="470"]`
- `QScrollArea#InlineQuickCreateFormScroll`
- `QFrame#InlineQuickCreateFormHolder`

### 6. Regression guards

Added:

- `tests/test_phase470_responsive_shell_fit.py`

The tests verify:

- TableToolbar uses two rows.
- Materials filters use a grid, not one long row.
- Floating quick-create forms are scrollable and solid.
- QSS includes the Phase470 responsive contracts.

## Verification

Executed:

```text
python -m compileall -q alrajhi_client tests
python tools/architecture_guard.py
python tools/phase422_i18n_rtl_quality_guard.py
pytest -q tests/test_phase457_runtime_visual_regression_gate.py tests/test_phase467_unified_floating_quick_create_system.py tests/test_phase468_floating_surface_transaction_layout.py tests/test_phase469_operational_surface_cleanup.py tests/test_phase470_responsive_shell_fit.py
```

Results:

```text
compileall: OK
architecture_guard: passed
i18n/RTL guard: 683 checks, failures=0
runtime/visual/floating/list-shell subset: 20 passed
```

## Notes

The next visual pass should be based on fresh screenshots from this Phase470 build. The most important screens to verify are:

- Materials list
- Material editor with `+ تصنيف`
- Sales invoice with `+ مادة`
- Purchase invoice with `+ مادة`
- POS with `+ المادة`
- Restaurant screen
