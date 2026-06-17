# Phase 28 — Restaurant Kitchen Display System (KDS)

## Scope
Added the first production-oriented kitchen display workflow on top of the Phase 27 restaurant ordering/payment flow.

## Implemented
- `KitchenDisplayWidget` touch UI for kitchen tickets.
- KDS ticket list with table and line count.
- Ticket detail view with all kitchen lines.
- Ticket status transitions: `sent`, `preparing`, `ready`, `served`, `cancelled`.
- Repository/gateway/service/API boundaries for KDS operations.
- Remote gateway endpoints for server mode.
- Arabic, English, German translations.
- QSS styling for the KDS panel.
- Regression tests for KDS lifecycle and UI/boundary wiring.

## Architectural notes
- HTTP/API remains thin.
- KDS SQL remains inside restaurant repositories/local gateway boundary.
- The restaurant dashboard now hosts three operational panes: tables, POS/order, kitchen display.

## Verification
- `architecture_guard`: passed.
- `pytest`: 27 passed, 1 old non-fatal warning.
- `compileall`: passed.
