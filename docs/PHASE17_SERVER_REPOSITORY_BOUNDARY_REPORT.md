# Phase 17 Server Repository Boundary Hardening

## Scope
This phase removes direct server API dependency on the generic `LegacySqlRepository` bridge for the remaining large API modules.

## Changed API modules
- `alrajhi_server/api/cashboxes.py`
- `alrajhi_server/api/invoices.py`
- `alrajhi_server/api/items.py`
- `alrajhi_server/api/manufacturing.py`
- `alrajhi_server/api/reports.py`
- `alrajhi_server/api/returns.py`
- `alrajhi_server/api/warehouses.py`

## Added domain repository boundaries
- `CashboxRepository`
- `InvoiceRepository`
- `ItemRepository`
- `ManufacturingRepository`
- `ReportRepository`
- `ReturnRepository`
- `WarehouseRepository`

## Guard hardening
`tools/architecture_guard.py` now rejects imports of `alrajhi_server.repositories.legacy_sql_repository` from `alrajhi_server/api/*`.

## Verification
- `python tools/architecture_guard.py`: passed
- `pytest -q`: passed, 2 tests, 1 pre-existing warning
- `python -m compileall -q alrajhi_client alrajhi_server tools tests`: passed
- cache directories removed before packaging

## Remaining technical debt
The large route modules still contain inline SQL strings and call `repository.query(...)`. The API no longer depends on the generic legacy repository, but the next phase should extract domain methods from these repositories so routes stop owning SQL text.
