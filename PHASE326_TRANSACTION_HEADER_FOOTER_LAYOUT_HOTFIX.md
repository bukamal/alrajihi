# PHASE 326 — Transaction Header/Footer Layout Hotfix

## Scope

This phase addresses the purchase/sales transaction layout issues visible in the runtime UI:

- Purchase and sales invoice fields above the line grid are collapsed into one compact inline row.
- Local document view controls are kept in the same row to avoid stacked, crowded header bands.
- Invoice footer summary is rendered horizontally beside a compact notes box.
- The same purchase/sales transaction layout structure is shared by both new purchase and new sales invoices.
- The material editor no longer renders the top identity card for the “new material” surface.

## Preserved contracts

- RTL/LTR layout remains controlled by Qt/application direction.
- Network/API mode is not bypassed; the phase is UI-layout only.
- Printing, currency policy, RBAC, multi-user behavior, restaurant, cafe, and apparel flows remain unchanged.
- The global workspace chrome remains the authoritative document title/action surface.

## Verification

- `tests/test_phase326_transaction_header_footer_layout_hotfix.py`
- Existing release gate and architecture checks.
