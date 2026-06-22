# Phase 328 — Dashboard POS & Transaction UX Polish

## Scope

This phase applies targeted runtime UX corrections after the apparel pricing hardening work:

- Expand dashboard card surfaces vertically and horizontally to reduce empty space.
- Center daily shortcut button text/icons and make shortcut buttons visually larger.
- Treat `Esc` as a global workspace command that returns to the dashboard from nested main/sub pages.
- Place POS issue warehouse and cashbox controls beside each other in one operational row.
- Tighten the shared sales/purchase transaction header so controls stay in a single compact row above the grid.
- Keep the invoice summary and notes as a compact horizontal footer below the line grid.

## Boundaries

The phase is UI-shell work only. It does not change document persistence, network/API behavior, RBAC, printing, currency conversion, inventory movements, apparel variants, restaurant or cafe execution logic.

## Verification

Covered by:

`tests/test_phase328_dashboard_pos_transaction_ux_polish.py`
