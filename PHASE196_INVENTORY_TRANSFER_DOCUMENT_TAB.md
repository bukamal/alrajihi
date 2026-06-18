# Phase 196 — Inventory Transfer Document Tab

Warehouse transfers now have a real workspace document tab instead of only a modal dialog.

Key changes:
- `InventoryTransferDocumentTab` extends `BaseDocumentTab`.
- Transfer lines use `TransactionLineGrid` via `InventoryTransferGrid`.
- Item cells use the shared `TransactionItemDelegate`; unit cells use the shared `TransactionUnitDelegate`.
- Manual lookup is case-insensitive through the shared catalog/barcode pipeline; scanner-like input remains exact.
- Unit barcode metadata is preserved: `unit_id`, `unit_name`, `conversion_factor`, `base_qty`, `barcode_scope`, `matched_barcode`.
- Local/server transfer persistence stores the unit/base-quantity fields.
- Inventory movements and ledger posting use `base_qty`, not display quantity.
- The warehouse workspace opens the document tab first, with legacy dialog fallback only if needed.
