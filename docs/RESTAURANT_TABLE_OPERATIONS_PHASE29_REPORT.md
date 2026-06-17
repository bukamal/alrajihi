# Restaurant Table Operations Phase 29

## Scope

Phase 29 adds operational table workflows required in daily restaurant use:

- Table reservations.
- Reservation cancellation.
- Moving an open session from one table to another.
- Merging two open table sessions.
- Splitting selected order lines to another table/session.

## Architecture

The HTTP layer remains thin. All SQL stays inside repository/gateway boundaries:

- `alrajhi_server/repositories/restaurant_repository.py`
- `alrajhi_client/gateways/local/restaurant_gateway.py`
- `alrajhi_client/gateways/remote/restaurant_gateway.py`
- `alrajhi_client/core/services/restaurant_service.py`

New server endpoints:

- `POST /api/restaurant/tables/<table_id>/reserve`
- `POST /api/restaurant/reservations/<reservation_id>/cancel`
- `POST /api/restaurant/sessions/<session_id>/transfer`
- `POST /api/restaurant/sessions/<target_session_id>/merge`
- `POST /api/restaurant/sessions/<session_id>/split_lines`

## Safety Rules

- A table cannot be reserved while occupied.
- A session cannot be transferred to an occupied table.
- Merging requires two open sessions.
- Splitting requires selected lines to belong to the source session.
- Splitting to a free target table opens a new target session automatically.

## Verification

- `architecture_guard`: passed.
- `pytest`: 29 passed, 1 existing non-fatal warning.
- `compileall`: passed.
- Cache files removed before packaging.
