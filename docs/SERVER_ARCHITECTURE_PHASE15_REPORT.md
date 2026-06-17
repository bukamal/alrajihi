# Server Architecture Phase 15

## Scope
Continued Phase 14 server-route remediation and processed the remaining five legacy API modules:

- `alrajhi_server/api/invoices.py`
- `alrajhi_server/api/items.py`
- `alrajhi_server/api/manufacturing.py`
- `alrajhi_server/api/reports.py`
- `alrajhi_server/api/returns.py`

## Change
Removed direct `get_db()` / SQLite connection imports from the remaining Flask API modules and routed database access through the transitional repository boundary:

- `alrajhi_server.repositories.legacy_sql_repository.get_legacy_sql_repository()`

The architecture guard allowlist was reduced to zero:

- `LEGACY_DB_ALLOWLIST = set()`
- `LEGACY_SQL_ALLOWLIST = set()`

## Verification
Executed successfully:

- `python tools/architecture_guard.py`
- `python -m compileall -q alrajhi_client alrajhi_server tests tools`
- `pytest -q`

Result:

- Architecture guard: passed with 0 tracked legacy exceptions.
- Compile: passed.
- Pytest: 2 passed, 1 existing non-fatal collection warning.

## Technical note
This phase completes the hard boundary removal from server API modules. The remaining SQL is still colocated as route-level statements passed to the transitional repository bridge. A later semantic refactor should split those statements into domain repositories such as `InvoiceRepository`, `InventoryRepository`, `ManufacturingRepository`, `ReturnRepository`, and `ReportRepository`.
