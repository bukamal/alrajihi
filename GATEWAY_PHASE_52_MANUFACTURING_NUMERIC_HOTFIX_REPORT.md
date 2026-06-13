# Phase 52 - Manufacturing Numeric Hotfix

## Problem
Creating a production order could crash in `ProductionOrderDialog.update_materials_display()` because manufacturing/BOM numeric values may arrive from SQLite/API as strings, while the UI formatted them directly with `:.2f`.

Example:

```text
ValueError: Unknown format code 'f' for object of type 'str'
```

## Fixes

- Added safe numeric conversion helper in `production_order_dialog.py`.
- Converted `required_qty` and `available_qty` before formatting.
- Converted insufficient-material warning values before formatting.
- Hardened `production_details_dialog.py` against string numeric values for:
  - consumed quantity
  - produced quantity
  - reserved quantity
  - remaining quantity
  - unit costs
  - planned/produced quantities

## Validation

- compileall: PASS
- architecture_guard: PASS
- reports_contract_check: PASS
- phase32_invoice_flow_guard: PASS
- offline_read_guard: PASS
- offline_widget_guard: PASS
- form_validation_guard: PASS
- zip test: PASS
