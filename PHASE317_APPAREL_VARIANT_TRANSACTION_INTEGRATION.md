# Phase 317 — Apparel Variant Transaction Integration

This phase connects the Phase 315/316 apparel variant foundation to operational transaction flows.

## Scope

- Invoice line payloads preserve `variant_id`, color, size, SKU, barcode scope, and matched barcode.
- POS fast-sale lines preserve variant identity and emit it into the normal sale invoice payload.
- Local and remote invoice persistence write variant metadata into `invoice_lines`.
- Inventory movements written by invoices carry variant metadata and refresh the related `item_variants.quantity` aggregate.
- Variant barcode lookup now reports availability from variant-specific movements, with variant quantity as fallback.
- The implementation remains inside the material/product engine. No apparel DAO/gateway/repository is introduced.

## Non-goals

- No separate apparel sales engine.
- No replacement of item units. Units remain quantity/packaging conversions.
- No changes to restaurant/cafe printing, currency, or runtime flows.

## Validation

The phase is guarded by `tests/test_phase317_apparel_variant_transaction_integration.py` and registered in the release gate contract.
