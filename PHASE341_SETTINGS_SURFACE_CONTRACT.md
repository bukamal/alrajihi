# Phase 341 — Unified Settings Surface Contract

This phase exposes the UI unification contracts through the settings layer.

## Scope

- Adds a PyQt-free settings surface contract for table-column settings and barcode profile settings.
- Adds a settings tab for UI/table/barcode contracts.
- Adds per-profile barcode controls for material, apparel, restaurant and cafe label profiles.
- Adds a reset action for column display/print/export defaults.
- Adds a release guard and audit matrix for the settings surface.

## Guarantees

- Column settings use `ui/columns/<page>/<table>/<column>/<visible|printable|exportable>`.
- Barcode profile settings use `printing/barcode/<sector>/<profile>/<field>`.
- Barcode printing remains Browser HTML only.
- Apparel barcode labels remain variant-based, not parent-material-based.
