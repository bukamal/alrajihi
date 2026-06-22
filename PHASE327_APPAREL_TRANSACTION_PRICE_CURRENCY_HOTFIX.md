# Phase 327 — Apparel Transaction Price Currency Hotfix

## Scope

This phase fixes a transaction pricing bug in apparel variant lookup rows.

When a base apparel item had a purchase or sale price in the current display currency and its color/size variants inherited that price, the transaction lookup row could be converted from storage currency to display currency twice. In Syrian-pound installations this produced extremely large invoice values, for example `20,000` becoming trillions.

## Changes

- Made transaction item price normalization idempotent through `_prices_in_display_currency`.
- Prevented the quick-search transform from converting an already-normalized apparel variant row again.
- Removed base-material names from variant lookup popup values so purchase/sales invoice suggestions show concrete color/size options, not a confusing standalone base material option.
- Prevented exact base-material name matching from choosing an arbitrary first apparel variant.
- Preserved variant barcode behavior: transaction rows keep the variant barcode and never fall back to the base material barcode.

## Expected behavior

- Purchase invoice for an apparel variant inherits the base item purchase price once only.
- Sales invoice for an apparel variant inherits the variant sale price or base item sale price once only.
- Searching by the base material name shows variant labels, but pressing add on the base name alone does not post an arbitrary variant.
- Users should select a concrete color/size label or scan the variant barcode.

## Guard

`tests/test_phase327_apparel_transaction_price_currency_hotfix.py`
