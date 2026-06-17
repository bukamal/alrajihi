# Phase125 Returns Unit Delegate + Delete Hotfix

## Scope
- Returns table unit column UX.
- Delete/cancel button activation in sales returns and purchase returns lists.
- Preservation of phase124 unit/quantity/price/accounting calculations.

## Changes
1. Replaced always-visible `QComboBox` widgets in the unit column with `ReturnUnitDelegate(QStyledItemDelegate)`.
2. Unit cells now display plain text by default and open a combo editor only while editing the unit cell.
3. Unit selection remains row-specific and stores selected unit metadata in `Qt.UserRole`.
4. Existing return calculations continue to use:
   - selected display quantity,
   - selected unit conversion factor,
   - base quantity validation,
   - price derived from original invoice line base price.
5. Enabled the delete/cancel toolbar button when a return row is selected in both sales and purchase returns.
6. Existing service deletion remains routed through `sales_return_service.delete_return` and `purchase_return_service.delete_return`, preserving stock/account/customer/supplier/cash reversal behavior.

## Verified
- No `setCellWidget(row, 4, QComboBox)` remains for return unit cells.
- Delegate is installed for sales-return dialog and purchase-return dialog.
- Delete button is activated on row click for both return lists.
- Phase124 return unit arithmetic test still passes.
- Compileall passes.

## Tests
- `python3 -m compileall -q alrajhi_client`
- `python3 tools/returns_unit_columns_deep_test_phase124.py`
- `python3 tools/phase125_returns_unit_delegate_delete_guard.py`
- `python3 tools/phase32_invoice_flow_guard.py`
- `python3 tools/verify_language_phase78_sales_purchases_returns.py`
