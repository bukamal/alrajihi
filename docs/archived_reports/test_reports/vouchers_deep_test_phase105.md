# Phase 105 — Vouchers deep accounting test and fixes

## Scope
- Receipt vouchers linked to sales invoices.
- Payment vouchers linked to purchase invoices.
- Expense vouchers.
- Invoice remaining amount and overpayment prevention.
- Customer/supplier balances.
- User cash balance.
- Cash/bank movement references.
- Update/delete reversals.
- UI auto amount fill from the selected invoice.

## Findings before fix
1. The voucher dialog showed invoice remaining amount in the combo label, but did not fill the amount field automatically.
2. Local voucher update deleted the old voucher and inserted a new one. This changed the voucher id and made the service record cash/bank movement against the old id.
3. Server voucher update also deleted and reinserted, returning a new id and breaking reference stability.
4. Server voucher inserts did not persist the full cash/bank fields: `cashbox_id`, `bank_account_id`, `payment_method`.
5. Server voucher path did not write `cash_bank_movements` for voucher operations.

## Applied fixes
- Added invoice selection auto-fill in `VoucherDialog.update_amount_from_invoice()`.
- Added edit-mode protection so loading an existing voucher does not overwrite its current amount automatically.
- Added remaining-amount calculation that includes the old voucher amount when editing the same linked invoice.
- Reworked local `update_voucher()` to update in place and preserve the voucher id.
- Reworked server voucher create/update/delete to:
  - preserve voucher id on update,
  - reverse old effects before update,
  - apply new effects after update,
  - persist cash/bank/payment fields,
  - create/delete `cash_bank_movements` with `reference_type='voucher'` and stable `reference_id`.

## Executed tests
- `python -m compileall -q alrajhi_client alrajhi_server tools`
- `python tools/vouchers_deep_accounting_test_phase105.py`
- `python tools/phase32_invoice_flow_guard.py`

## Accounting scenarios verified

### Sales receipt voucher
Initial invoice: total 1000, paid 200, customer balance 800.
- Add receipt 300:
  - invoice paid = 500
  - customer balance = 500
  - user cash = 300
  - cash movement = +300
- Overpayment 600 rejected while remaining is 500.
- Update same voucher to 500:
  - same voucher id preserved
  - invoice paid = 700
  - customer balance = 300
  - user cash = 500
  - exactly one cash/bank movement remains for the same voucher id
- Delete voucher:
  - invoice paid returns to 200
  - customer balance returns to 800
  - user cash returns to 0
  - movement is removed

### Purchase payment voucher
Initial invoice: total 1200, paid 400, supplier balance 800.
- Add payment 350:
  - invoice paid = 750
  - supplier balance = 450
  - user cash = -350
  - cash movement = -350
- Update same voucher to 800:
  - invoice paid = 1200
  - supplier balance = 0
  - user cash = -800
- Delete voucher:
  - invoice paid returns to 400
  - supplier balance returns to 800
  - user cash returns to 0

### Expense voucher
- Add expense 77:
  - user cash = -77
  - cash movement = -77
  - no customer/supplier/invoice relation is allowed.

## Result
PASS. Voucher accounting, update/delete reversals, reference stability, cash/bank movements, and invoice-based automatic amount fill are now covered by regression tests.
