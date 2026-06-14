# Phase 62 - Invoice Units/Table Hotfix

## Scope
Fix invoice line-table issues in sales/purchase windows:

- item name disappearing after loading/editing invoices;
- sub-unit selection not recalculating price/total correctly;
- conversion factors arriving as strings from DB/API;
- invoice line payload missing `item_name`, reducing resilience across Local/Remote flows.

## Changes

### `views/dialogs/invoice_dialog.py`
- Added safe Decimal helpers:
  - `_decimal_value()`
  - `_positive_decimal()`
- Normalized unit conversion factors when setting invoice line units.
- Added robust `item_name` fallback while loading invoice lines:
  - `item_name`
  - `name`
  - `product_name`
  - `itemName`
  - `productName`
  - fallback from `product_service.item_by_id()`
- Included `item_name` in invoice line save payload.
- Normalized loaded values for:
  - quantity
  - unit price
  - total
  - discount
  - tax
- Hardened row-total calculation against string numeric values.

### `views/dialogs/invoice_delegates.py`
- Fixed sub-unit price recalculation.
- Previous bug: delegate updated column `4`, which is the unit column.
- Now uses:
  - `model.COL_PRICE` with fallback to column `5`.
- Recalculates unit price by conversion-factor ratio:
  - old price × new factor / old factor.
- Normalizes old/new factors and prices to Decimal before arithmetic.

### New guard
Added:

```text
tools/invoice_units_guard.py
```

Checks:

- item name fallback exists;
- invoice payload keeps item name;
- conversion factor is normalized;
- delegate updates price column, not unit column;
- unit factors are Decimal-safe.

## Validation

```text
compileall: PASS
architecture_guard: PASS
reports_contract_check: PASS
phase32_invoice_flow_guard: PASS
offline_read_guard: PASS
offline_widget_guard: PASS
form_validation_guard: PASS
manufacturing_numeric_guard: PASS
manufacturing_ui_guard: PASS
print_action_guard: PASS
verify_branding_assets: PASS
invoice_units_guard: PASS
zip test: PASS
```

## Expected Behavior

When selecting a material in sales/purchase invoice tables:

- material name remains visible after save/reopen/edit;
- changing from base unit to sub-unit updates the displayed unit price;
- row total changes immediately according to selected unit;
- saved payload preserves display quantity + selected unit + base quantity.
