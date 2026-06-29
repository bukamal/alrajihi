# Phase 448 — Operational POS & Restaurant Surface Migration

This phase applies the project visual identity to the operational workspaces that were still visually distinct after the shell/list sweeps: POS, Restaurant order entry, and Restaurant Simple POS.

## Scope

- POS remains barcode/table-first; material cards are not restored.
- Restaurant/Cafe continue to use the shared operational item card grid.
- Business logic, checkout, printing, inventory, permissions, and Enter navigation are untouched.

## Changes

- Added Phase 448 operational design tokens in `theme/brand.py`.
- Added QSS overrides for `operationalSurfacePhase="448"` after the older Basit operational selectors.
- Bound POS scan input, table, payment shell, warehouse/cashbox context, and actions to semantic visual roles.
- Bound Restaurant Simple POS header, panels, category cards, table, footer, total, and checkout actions to semantic visual roles.
- Bound Restaurant POS header, search panel, summary, order grid, action bar, and menu toggle to the same operational identity layer.
- Removed local barcode scan `setStyleSheet()` from POS and replaced it with font sizing plus centralized QSS.

## Acceptance

- POS opens as a clean barcode/table-first operational screen.
- Restaurant Simple POS sections no longer rely on strong yellow/blue legacy visual blocks.
- Restaurant POS primary actions and order grid align with the same operational identity.
- Guards protect the shared roles and prevent reverting the POS barcode field to local QSS.
