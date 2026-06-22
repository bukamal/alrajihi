# Phase 318 — Workspace Shell & Transaction Layout Unification

This phase aligns global shell chrome and high-frequency transaction surfaces before continuing apparel operations.

## Scope

- Kept product/apparel internal fields stable while replacing the visible `SKU` label with localized variant-code wording.
- Compacted the icon navigation bar to avoid left-side overlap on minimum supported widths and in RTL/LTR modes.
- Hid the unified action strip on the dashboard while preserving it for operational workspaces.
- Removed redundant top identity cards from the material dialog and transaction documents.
- Made sales/purchase transaction line grids full-width, with compact notes and totals below the grid.
- Added context-aware payment wording: sales show “received”; purchases show “paid”.

## Guardrails

- No direct data access was added to UI surfaces.
- API/network mode, multi-user behavior, currency formatting, printing, and RBAC remain unchanged.
- Internal variant schema remains compatible with Phase 315–317.
