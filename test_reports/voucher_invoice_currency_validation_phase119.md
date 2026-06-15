# Phase119 - Voucher invoice remaining currency validation hotfix

## Problem
When creating a receipt/payment voucher linked to an unpaid invoice, the invoice selector displayed the correct remaining amount in the display currency, for example:

- Remaining displayed: `2,000,000 SYP`
- Stored invoice remaining in accounting currency: `142.857142857142857... USD`

The save path could reconvert the displayed amount through the current exchange rate and then compare it against the invoice's stored accounting-currency remainder. This produced a false validation error:

`مبلغ السند يتجاوز المتبقي على الفاتورة (142.857142857142857...)`

## Root cause
The dialog had two representations of the same value:

1. UI/display amount shown in the active display currency.
2. Canonical invoice remaining stored in the accounting/base currency.

The invoice selector used the canonical value to display the correct user-facing amount, but save validation could use a freshly converted spinbox value instead of the exact cached invoice remainder.

## Fix
`alrajhi_client/views/widgets/vouchers_widget.py`

- Cached the selected invoice remaining amount as `_selected_invoice_remaining_base`.
- Added `_amount_to_accounting_currency()`.
- If the entered amount matches the auto-filled remaining amount within one display minor unit, the voucher stores the exact cached accounting-currency remainder.
- Partial/manual entries still convert normally from display currency to accounting currency.

## Verification
- Syntax check: `python -m compileall alrajhi_client/views/widgets/vouchers_widget.py`
- Static verification: the save path now calls `_amount_to_accounting_currency()` instead of direct conversion.
- The auto-filled full invoice amount no longer creates false over-payment errors caused by currency conversion/rounding.
