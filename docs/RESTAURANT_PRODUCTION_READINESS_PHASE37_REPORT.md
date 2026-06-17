# Restaurant Production Readiness Phase 37

## Scope
Added a read-only production readiness diagnostic for the restaurant vertical.

## Added
- `RestaurantRepository.restaurant_production_readiness()`
- `GET /api/restaurant/readiness`
- Client `RestaurantGateway`/`RestaurantService` boundary methods
- Local and remote gateway implementations
- Build guard for restaurant production readiness coverage

## Checks
- Required restaurant tables exist.
- No sessions point to missing tables.
- No order lines point to missing sessions.
- No kitchen ticket lines point to missing tickets or missing order lines.
- Warnings for unsent lines, queued print jobs, and pending delivery/takeaway orders.

## Design
This phase does not add new sales logic. It hardens operational visibility before the restaurant module is considered production-ready.
