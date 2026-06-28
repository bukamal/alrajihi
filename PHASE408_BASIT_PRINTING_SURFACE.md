# PHASE408 — Basit Printing Surface

## Scope
This phase aligns browser HTML printing output with the Basit-inspired runtime UI that was introduced in phases 401–407.

## Implemented
- Added a `_basit_print_tokens()` bridge inside `alrajhi_client/printing/print_templates.py`.
- Browser HTML print templates now read Basit palette values from `theme.brand` tokens instead of using the old generic accent skin.
- Invoice, return, voucher, report, restaurant, manufacturing, inventory and POS receipt prints now share:
  - blue company/document chrome,
  - yellow active/document badge accents,
  - red final total rows,
  - Basit-like table header/grid surfaces,
  - Basit-like summary cards and notes blocks.
- Thermal receipt output keeps compact/no-shadow behavior while inheriting Basit print markers where safe.

## Non-goals
- No accounting logic changes.
- No currency conversion changes.
- No printer routing changes.
- No document payload/schema changes.

## Verification
- `tools/phase408_basit_printing_surface_guard.py`
- `tests/test_phase408_basit_printing_surface.py`
