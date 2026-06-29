# Phase 437 — Dashboard Visual Identity Alignment

This phase aligns the dashboard visual surface with the branded startup splash,
horizontal login, and operational screens without changing accounting, cashbox,
shortcut, or dashboard refresh logic.

## Goals

- Replace the old hard Basit-style dashboard card borders with identity-aligned surfaces.
- Reduce the visual weight of the yellow header strips.
- Keep three dashboard columns: daily shortcuts, company identity, and cashbox.
- Keep all dashboard actions, cashbox privacy controls, currency controls, and refresh logic intact.
- Centralize dashboard colors and sizing through brand tokens.

## Key changes

- Added Phase 437 dashboard design tokens in `theme/brand.py`.
- Updated `DashboardPanel` and `QuickActionButton` in `views/widgets/dashboard_legacy_components.py`.
- Updated `DashboardWidget` styling for the main dashboard, daily shortcuts, company card, cashbox card, cash movement metrics, current balance, and developer brand band.
- Added a Qt-free quality contract and guard.

## Runtime intent

The dashboard remains functionally the same, but visually moves away from flat strong blue/yellow blocks toward the same calm blue/teal identity used by the login and splash screens.

## Verification

Run:

```bash
python tools/phase437_dashboard_visual_identity_guard.py
pytest tests/test_phase437_dashboard_visual_identity_alignment.py
```
