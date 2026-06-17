# Phase 18 — Server API Boundary Completion

## Scope
This phase hardens the server architecture after Phase 17 by making `alrajhi_server/api` a strict HTTP boundary. API modules now expose/import Blueprints only and are guarded against direct SQL execution and SQL literals.

## Applied changes
- Moved large SQL-bearing route implementations out of `alrajhi_server/api` into `alrajhi_server/services/http_routes`:
  - `cashboxes.py`
  - `invoices.py`
  - `items.py`
  - `manufacturing.py`
  - `reports.py`
  - `returns.py`
  - `warehouses.py`
- Replaced the API files above with thin wrapper modules that only export the Blueprint.
- Removed `LegacySqlRepository` and replaced it with `SqlRepository` in `base_sql_repository.py`.
- Updated domain repositories to depend on the neutral repository-layer SQL base instead of the legacy bridge.
- Strengthened `tools/architecture_guard.py`:
  - forbids `.query(...)` as direct SQL access in protected layers;
  - forbids SQL literals inside `alrajhi_server/api` wrappers;
  - keeps legacy allowlists empty.
- Removed stale cache artifacts after verification.

## Verification
- `python tools/architecture_guard.py`: passed.
- `python -m compileall -q alrajhi_client alrajhi_server tools tests`: passed.
- `pytest -q`: passed, 2 tests, 1 pre-existing non-fatal collection warning.

## Remaining technical debt
The API package is now clean. Some SQL still exists in `alrajhi_server/services/http_routes` through domain repositories. The next precision step is to split those SQL workflows into semantic repository methods rather than route-service calls to `repository.query(...)`.
