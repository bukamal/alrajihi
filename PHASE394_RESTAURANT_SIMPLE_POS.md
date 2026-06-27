# Phase 394 — Restaurant Simple POS

The restaurant workspace is now a simple selling interface named **واجهة مطعم**.

## Contract

- Default restaurant page routes to `RestaurantSimplePOSWidget`.
- The operator surface has three sections only: categories, items, and current invoice.
- Invoice columns are item name, quantity, unit price, total, and notes.
- The visible kitchen, KDS, table map, analytics, transfer, merge and reservation controls are not part of the default restaurant page.
- Checkout uses the restaurant/POS engine and posts a normal sale invoice through `checkout_simple_pos_session`.
- New lines are marked served internally before checkout; no kitchen ticket is created for simple POS.

## Notes

Legacy restaurant operational widgets remain in the codebase for historical/cafe compatibility, but the restaurant navigation entry opens the simplified POS surface.
