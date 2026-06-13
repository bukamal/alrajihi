# GATEWAY PHASE 28 REPORT

## Scope
Phase 28 adds a controlled Inventory Ledger backfill facility. This is migration-preparation only and does not make the ledger authoritative.

## Implemented
- `InventoryLedgerDAO.backfill_from_inventory_movements(...)`
- `InventoryGateway.ledger_backfill(...)` contract
- `LocalInventoryGateway.ledger_backfill(...)`
- `RemoteInventoryGateway.ledger_backfill(...)`
- `InventoryService.ledger_backfill(...)`
- `RestClient.inventory_ledger_backfill(...)`
- `POST /api/inventory-ledger/backfill` on the server

## Behavior
- Default mode is `dry_run=True`.
- Backfill source is legacy `inventory_movements`.
- Created ledger rows are item-level only with `warehouse_id=NULL`.
- Idempotency is enforced using `source_table='inventory_movements'` and `source_id`.
- `clear_existing=True` is available only when `dry_run=False`; it removes previous backfill rows for the same source before rebuilding.
- No operational stock values are changed.

## Validation
- `python3 -m compileall -q alrajhi_client alrajhi_server`: passed.
- `python3 tools/architecture_guard.py`: passed.

## Recommended usage
1. Run `inventory_service.ledger_backfill(dry_run=True)` and inspect counts/preview.
2. If the preview is acceptable, run `inventory_service.ledger_backfill(dry_run=False)`.
3. Run `inventory_service.ledger_reconciliation(tolerance='0')`.
4. Do not switch stock calculations to ledger until mismatches are reviewed.

## Next phase
Phase 29 should add a safer reconciliation UI/report export and a backfill audit screen before enabling any live ledger authority.
