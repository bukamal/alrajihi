# Phase 100.1 – Cash Card Layout Rollback

## Scope
Partial rollback only for the Dashboard cash card layout introduced in Phase 100.

## Kept from Phase 100
- First dashboard card under global search remains removed.
- Refresh button remains beside notifications/theme/screenshot controls.
- Enlarged navigation icons remain.
- Navigation labels under icons remain.
- Home icon remains without label.

## Rolled back
- Cash card movement layout restored to pre-Phase-100 grid layout.
- Current cash balance layout restored to horizontal layout.
- Display currency/exchange-rate layout restored to grid layout.

## Validation
- `python3 -m compileall -q alrajhi_client` passed.
