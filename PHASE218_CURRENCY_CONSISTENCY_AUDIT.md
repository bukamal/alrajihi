# Phase 218 — Currency Consistency Audit

This phase hardens the unified currency contract across the post-tabification UI.

## Goals

- Avoid new direct `USD` assumptions in unified UI/model paths.
- Keep persisted monetary amounts in the configured storage/base currency.
- Convert UI-entered amounts back to base before service/gateway persistence.
- Format displayed amounts with the active display currency.

## Changes

### CurrencyManager helpers

Added convenience helpers in `alrajhi_client/currency.py`:

- `storage_currency()`
- `display_currency()`
- `to_display()`
- `from_display()`
- `format_display_amount()`
- `format_base_amount()`

These preserve backward compatibility while giving newer code a stable API that
does not hard-code `USD`.

### Updated unified UI paths

Adjusted the following areas to use the helper contract:

- Voucher/expense payment panel
- Voucher invoice-link remaining amount display
- POS line grid money display
- POS payment/shift money conversion
- Restaurant order grid money display
- Restaurant POS totals, manual line price, adjustments, and payments
- Manufacturing lifecycle cost entry/display
- Cashbox/bank/shift/movement display amounts

### Restaurant POS correction

Restaurant session balances are stored in base currency. The UI now:

- Displays subtotal/discount/service/tax/total/paid/remaining in the active display currency.
- Converts adjustment and payment input from display currency back to base before calling the service.
- Converts manual line unit price from display currency back to base.

## Guard

Added:

`tools/phase218_currency_consistency_guard.py`

The guard verifies:

- The unified currency helper API exists.
- Critical unified UI/model files do not reintroduce direct `USD` literals.
- Restaurant POS input/output paths perform display/base conversion.
- Voucher payment panel uses `to_display()` / `from_display()`.
