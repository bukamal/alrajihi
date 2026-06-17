# GATEWAY PHASE 129 - Returns Edit Button

## Scope
Added an edit action for sales returns and purchase returns without changing the existing route structure.

## Implemented
- Enabled toolbar edit button in both returns lists.
- Edit opens the return dialog with the original invoice locked.
- Existing return lines are loaded back with selected unit, quantity, price, refund, warehouse, cashbox/bank and notes.
- Current return quantity is added back to the returnable quantity during edit so validation remains correct.
- Save in edit mode calls `update_return`.
- `update_return` was added to service and gateway contracts.
- Local update uses the existing accounting-safe reversal/create pipeline and preserves the return number for continuity.
- Remote gateway includes a compatible replacement update path.
- Added Arabic, English, and German language keys for edit/update/updated return.

## Validation
- compileall: PASS
- returns_unit_columns_deep_test_phase124: PASS
- phase125_returns_unit_delegate_delete_guard: PASS
- phase32_invoice_flow_guard: PASS
- invoice_phase108_integrity_guard: PASS
- qt_signal_method_guard: PASS
- verify_language_phase78_sales_purchases_returns: PASS
- verify_phase89_secondary_localization: PASS

## Note
The edit operation is intentionally routed through accounting reversal and recreation instead of mutating stock/cash balances in place. This preserves the same validated business paths used by delete and create.
