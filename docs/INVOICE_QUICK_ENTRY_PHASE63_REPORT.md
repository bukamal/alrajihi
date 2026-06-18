# Phase 63 — Invoice Quick Entry UX

## Scope
This phase improves the daily sales/purchase invoice workflow after the enterprise grid work.

## Added
- Quick quantity spin box beside barcode/item search.
- Barcode scan now increments an existing line by the selected quick quantity instead of always `1`.
- New item quick-add applies the selected quantity immediately.
- `F6` focuses the quick quantity field.
- Live invoice grid status row: active lines, total quantity, visible columns, and issue count.
- Row-level validation feedback with tooltip/background for unresolved items, invalid quantity/price, or missing unit.

## Preserved
- Unified printing.
- SmartTableView column chooser/layout behavior.
- Invoice bottom action bar.
- Service/Gateway boundaries.

## Guard
`tools/phase63_invoice_quick_entry_guard.py`
