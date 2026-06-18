# Phase 48 — Invoice Document Tab Refactor + Item Units Restoration

## Scope
This phase continues the Document Tabs migration by extracting explicit invoice document boundaries and restoring item unit maintenance inside the item editor tab.

## Invoice document boundaries
Added reusable invoice components:

- `InvoiceHeaderComponent`
- `InvoiceLinesComponent`
- `InvoicePricingEngine`
- `InvoicePaymentsComponent`
- `InvoiceActionsComponent`

The existing proven invoice UI remains operational, while workspace-level code now has explicit component boundaries instead of reaching into dialog internals.

## Unit-aware invoice payload
`InvoiceDialog` now exposes `invoice_document_payload()`, returning:

- header data
- unit-aware line payload
- pricing summary
- paid amount

Invoice lines retain:

- selected unit
- `unit_id`
- `conversion_factor`
- `base_qty`

## Item units restored
`ItemEditorTab` now includes a units table for alternate units and conversion factors. Saved items persist units through `product_service.replace_units()`.

## Guards
Added:

- `tools/document_tabs_phase48_guard.py`

It verifies:

- invoice components exist
- invoice dialog installs components
- invoice payload exists
- invoice lines are unit-aware
- item editor exposes and persists units

## Verification
Passed:

- `architecture_guard.py`
- `document_tabs_guard.py`
- `document_tabs_phase47_guard.py`
- `document_tabs_phase48_guard.py`
- `phase32_invoice_flow_guard.py`
- `phase32_windows_import_guard.py`
- `restaurant_production_readiness_guard.py`
- `smart_table_rollout_guard.py`
- `unified_printing_guard.py`
- `dashboard_modernization_guard.py`
- `notification_center_guard.py`
- `pytest`: 75 passed
- `compileall`: passed
