# Phase 30 — Restaurant Waiter Workflow

Implemented waiter workflow primitives on top of Phase 29.

## Added
- Assign waiter to an open table session.
- Call waiter from a table session.
- Resolve waiter call.
- Session-level service summary with minutes open, modification count, cancellation count, and event counts.
- `restaurant_service_events` audit trail for waiter/session actions.
- Local and remote gateway contract coverage.
- Server HTTP endpoints without SQL in HTTP layers.
- Arabic, English, and German translation keys.

## Boundary
SQL remains inside restaurant repositories/local gateways only. API, HTTP route services, and UI remain thin wrappers.
