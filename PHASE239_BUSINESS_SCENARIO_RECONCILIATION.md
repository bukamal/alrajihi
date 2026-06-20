# Phase 239 — Business Scenario Reconciliation Tests

## Goal
Execute a real cross-module local business scenario and fix any problems discovered across materials, units, warehouse balances, invoices, vouchers, returns, manufacturing, cashbox movements, and reports.

## Scenario executed
- Created materials with opening quantity, without opening quantity, and with sub-units.
- Created a customer and supplier.
- Created partial and fully paid purchase invoices.
- Created partial and fully paid sales invoices.
- Created receipt and payment vouchers linked to invoices.
- Created partial sales and purchase returns.
- Created BOM with a sub-unit component and a base-unit component.
- Created, started, consumed, and completed a production order.
- Reconciled final warehouse balances, invoice paid totals, cashbox totals, manufacturing reports, product cost reports, and invoice profit reports.

## Problems found and fixed

### 1. Sub-units submitted with add_item were not persisted
`ProductService.add_item()` validated `units` but did not persist them unless the UI separately called `replace_units()` afterward. Headless/API/import-style material creation could lose sub-units.

Fixed by persisting `units` inside `ProductService.add_item()` after item creation.

### 2. Opening quantities were not available in warehouse balances after material creation
If the default warehouse existed before adding a material with opening stock, `WarehouseRepository.bootstrap_defaults()` saw an opening `inventory_movements` row and seeded the warehouse balance as zero to avoid double counting. This made warehouse availability ignore opening quantities.

Fixed by distinguishing opening-only movements from transactional movements. Opening-only material rows now seed the default warehouse with the opening quantity.

### 3. Immediate invoice paid amounts did not reach cash/bank movement reports
Invoice creation updated legacy `users.cash_balance`, but modern dashboard/reports read `cash_bank_movements`. Paid sale/purchase invoices therefore did not appear in cashbox totals until a voucher was created.

Fixed by adding `CashboxService.record_invoice_payment()` and wiring it into `InvoiceService.create/update/delete`.

### 4. Manufacturing completion tried to write obsolete journal columns
Manufacturing completion used legacy accounting columns `date`, `reference_type`, `reference_id`, `entry_id`, and `account_code`, while the current accounting schema uses `entry_date`, `source_type`, `source_id`, `journal_entry_id`, and `account_id`.

Fixed by making manufacturing accounting posting schema-aware and optional. Production completion no longer fails if accounting schema differs.

### 5. Local reporting gateway branch helper/signatures were incomplete
`LocalReportingGateway` used `_effective_branch_id()` without defining it. This caused several reports, including invoice profitability, to silently return empty results. Manufacturing and product cost report signatures also drifted from the service contract.

Fixed by adding `_effective_branch_id()` and aligning report method signatures/queries.

## Guard added
`tools/phase239_business_scenario_reconciliation_guard.py`

It creates a fresh local database and asserts:
- Opening materials are visible in warehouse balances.
- Sub-units submitted with material creation are persisted.
- Partial/full sales and purchases affect inventory and cashbox ledgers.
- Linked receipt/payment vouchers update invoice paid totals and cashbox movements.
- Partial returns reconcile inventory.
- BOM and production order recognize and consume raw materials.
- Final balances are exactly:
  - Raw A = 15
  - Raw B = 18
  - Raw C = 10
  - Finished product = 2
- Cash total = 61
- Invoice profit report, manufacturing report, and product cost report return relevant rows.

## Validation
Executed successfully:
- `python tools/phase239_business_scenario_reconciliation_guard.py`
- `python tools/phase238_manufacturing_bom_material_recognition_guard.py`
- `python tools/phase237_browser_html_print_guard.py`
- `python tools/phase236_print_settings_contract_guard.py`
- `python tools/phase235_unified_print_button_guard.py`
- `python tools/phase233_full_unification_guard.py`
- `python tools/phase232_project_language_audit.py`
- `python tools/phase234_dashboard_cashbox_runtime_guard.py`
- `python tools/reports_contract_check.py`
- `python tools/advanced_runtime_test.py`
- `python -m compileall -q alrajhi_client alrajhi_server`
