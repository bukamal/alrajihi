# Phase 49 — Returns Document Tabs

## Scope

Sales and purchase returns were moved from the Phase 47 generic `DialogDocumentTab` bridge to feature-level document tabs.

## Implemented boundaries

- `SalesReturnEditorTab`
- `PurchaseReturnEditorTab`
- `ReturnHeaderComponent`
- `ReturnLinesComponent`
- `ReturnSettlementComponent`
- `ReturnActionsComponent`

## Unit-system preservation

Return line payloads remain unit-aware and keep:

- `quantity`
- `quantity_in_base`
- `conversion_factor`
- `unit`
- `unit_id`
- unit-price normalization through the existing return pricing helpers

This keeps invoice units, inventory base quantities, and return validation aligned.

## Workspace behavior

The return tabs expose:

- `workspace_save()`
- `workspace_print()`
- `workspace_export()`
- `document_payload()`
- `dirtyChanged`
- `saved`
- `titleChanged`

## Guard

`tools/document_tabs_phase49_guard.py` prevents returns from falling back to the generic dialog bridge and checks the unit-aware payload boundary.
