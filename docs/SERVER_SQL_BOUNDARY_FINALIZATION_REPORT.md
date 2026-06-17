# Server SQL Boundary Finalization Report

## Scope
This phase finalizes the server HTTP boundary cleanup after Phase 18.

## Result
- `alrajhi_server/api` is a thin HTTP boundary.
- `alrajhi_server/services/http_routes` is now also a thin HTTP/service boundary.
- SQL literals and direct `.query/.execute/.executemany/.executescript` calls are forbidden in both layers by `tools/architecture_guard.py`.
- SQL-backed route implementation has been moved out of protected HTTP/service wrapper layers into repository-owned modules under `alrajhi_server/repositories/http_route_sql`.
- `LegacySqlRepository` is not referenced.

## Verification
- `python tools/architecture_guard.py` passes.
- `python -m compileall -q alrajhi_client alrajhi_server tools tests` passes.
- `pytest -q` passes with 2 tests and one pre-existing non-fatal pytest collection warning.

## Remaining technical note
The large ERP route families still contain route handlers co-located with SQL-backed repository implementation under `repositories/http_route_sql`. This removes SQL from HTTP/service boundaries and makes the guard enforceable. A later refinement may split these into smaller use-case methods per endpoint, but the direct boundary violation is closed.
