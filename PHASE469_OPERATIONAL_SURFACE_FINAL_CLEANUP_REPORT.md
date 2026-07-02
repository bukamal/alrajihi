# Phase469 — Operational Surface Final Cleanup

## Scope

Phase469 continues from Phase468 and focuses on the remaining visual/runtime issues visible in the user screenshots:

- Floating Quick Create cards occasionally rendering transparent or without a solid surface.
- POS top/scan/payment areas still consuming too much vertical space and clipping the payment footer on smaller screens.
- POS quick-create drawer placement needing a stable RTL-safe side and scan-bar-safe anchor.
- Restaurant Simple POS header still being a single crowded row that clips controls on 1024px screens.

No business logic, accounting logic, database schema, service/gateway behavior, permissions model, or feature set was removed.

## Implemented changes

### 1. Floating Quick Create hardening

Files:

- `alrajhi_client/ui/floating_quick_create.py`
- `alrajhi_client/ui/inline_quick_create.py`
- `alrajhi_client/theme/qss.py`

Changes:

- Floating panels now set QSS-driving properties before styling is applied.
- Panels explicitly disable translucent and no-system background modes:
  - `WA_TranslucentBackground = False`
  - `WA_NoSystemBackground = False`
  - `setAutoFillBackground(True)`
  - `setWindowOpacity(1.0)`
- Added direct object selector styling in addition to property-based styling.
- Added stronger drop shadow and forced style repolish/update.
- Added Phase469 marker: `floatingSurfacePhase=469`.
- Kept Phase468 compatibility markers to avoid breaking existing visual regression tests.

Result:

- The floating quick-create card should now render as a solid card/drawer instead of appearing transparent or blending with the page.

### 2. POS operational cleanup

Files:

- `alrajhi_client/views/widgets/pos_widget.py`
- `alrajhi_client/features/pos/pos_payment_shell.py`
- `alrajhi_client/theme/qss.py`

Changes:

- Added `posOperationalCleanupPhase=469`.
- Reduced POS layout margins/spacings.
- Reduced scan field height/font size from oversized runtime values to a more stable cashier size.
- Reduced POS table minimum height so the payment footer is not clipped on lower-height screens.
- Added `posPaymentCompactPhase=469` and maximum footer height.
- POS payment title is hidden in compact mode because it consumes cashier space.
- Payment actions are arranged in one compact row instead of two tall rows.
- POS Floating Quick Create drawer is explicitly anchored below the scan bar.
- RTL drawer placement fixed: Arabic/RTL POS drawer opens from the right side of the POS surface.

Result:

- POS should show less vertical crowding above the scan field.
- The payment/footer buttons should no longer be clipped at the bottom.
- Quick-create drawers should not push or cover the scan bar.

### 3. Restaurant Simple POS header cleanup

File:

- `alrajhi_client/views/restaurant/restaurant_simple_pos_widget.py`

Changes:

- Added `restaurantOperationalCleanupPhase=469`.
- Split the single crowded restaurant header row into:
  - title row
  - search row
  - action row
- Reduced footer button height/width.
- Adjusted splitter sizes to give the invoice area more stable room.

Result:

- Restaurant Simple POS should avoid clipping header buttons such as search, new sale, refresh, category, item, and fullscreen.

## Verification

Commands run:

```bash
python -m compileall -q alrajhi_client tests
python tools/architecture_guard.py
python tools/phase422_i18n_rtl_quality_guard.py
python tools/phase457_runtime_visual_regression_gate.py
pytest -q \
  tests/test_phase467_unified_floating_quick_create_system.py \
  tests/test_phase468_floating_surface_transaction_layout.py \
  tests/test_phase469_operational_surface_cleanup.py \
  tests/test_phase466_pos_toolbar_fullscreen_cleanup.py \
  tests/test_phase430_pos_barcode_table_first.py \
  tests/test_phase394_restaurant_simple_pos.py \
  tests/test_phase465_visual_shell_unification.py
```

Results:

```text
compileall: OK
architecture_guard: passed
i18n/RTL guard: 683 checks, failures=0
runtime visual regression gate: pass, 24 checks
Phase467/468/469 + POS/Restaurant/Visual subset: 33 passed
Phase459–469 focused subset: 45 passed
```

## Runtime note

This phase is visual/layout hardening. The final judgment must be made from actual Windows runtime screenshots after opening:

- POS normal mode
- POS fullscreen mode
- POS + مادة drawer
- POS + صندوق drawer
- Restaurant Simple POS
- Material editor + تصنيف popover
- Sales/Purchase document quick-create drawer

If any drawer still needs pixel-level placement adjustment on the target display, Phase470 should be a targeted runtime screenshot correction pass.
