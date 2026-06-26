# Phase 387 — Invoice & Return List Actions

This phase hardens the Edit/Delete actions for sales invoices, purchase invoices, sales returns and purchase returns.

## Scope

- Sales invoice list.
- Purchase invoice list.
- Sales return list.
- Purchase return list.

## Runtime guarantees

- Toolbar Edit/Delete actions resolve the current selected source row, not a stale visible/proxy row.
- Double-click Edit maps proxy indexes back to the source model.
- Invoice Edit opens the correct sale/purchase document using `open_quick_invoice(inv_type, invoice_id=...)`.
- Invoice Delete checks linked vouchers and linked returns before asking for confirmation.
- Invoice Delete refreshes only the affected invoice list after success.
- Return Edit/Delete buttons are driven by `selectionChanged`, not by blind click-enabling.
- Return Edit/Delete actions honor `ACTION_EDIT_RETURNS` and `ACTION_DELETE` permissions.
- Return actions show feedback when no row is selected.

## Guard

- `tools/phase387_invoice_return_list_actions_guard.py`
- `tests/test_phase387_invoice_return_list_actions.py`
- `alrajhi_client/workspace/quality/invoice_return_list_actions_contract.py`
