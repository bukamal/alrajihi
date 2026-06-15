# Phase121 - Returns Item Name and Quantity Formatting Fix

## Issue
In sales/purchase return dialogs, the item column showed the numeric `item_id` instead of the item name when `invoice_lines.description` was empty. Also, the `previous_returned` column could display scientific notation such as `0E+1`, which confused users.

## Root Cause
1. `/api/returns/*/invoices/<id>/lines` returned raw `invoice_lines` rows without joining the `items` table. If the invoice line description was empty, the UI fell back to `item_id`.
2. Decimal values were converted with `str(Decimal(...))`. Values like `Decimal('0E+1')` or `Decimal('1E+1')` can render as scientific notation.

## Fix
- Server: `_invoice_lines()` now joins `items` and returns `description` as `COALESCE(invoice_lines.description, items.name, item_id)` plus `item_name`.
- Server: added `_fmt_dec()` to serialize all return quantities in plain decimal form.
- Client: returns table now formats quantities with `_plain_number()` and uses `_return_item_name()` instead of falling back directly to `item_id`.

## Covered Columns
- المادة / return_item
- كمية المشترى / purchased_qty
- كمية المباع / sold_qty
- مرتجع سابق / previous_returned
- القابل للإرجاع / returnable_qty

## Validation
- `python3 -m compileall` passed for `alrajhi_client` and `alrajhi_server`.
- Static verification confirmed the new server join and no-scientific-notation helpers are present.
