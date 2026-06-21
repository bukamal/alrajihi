# Phase 299 — Restaurant Order Workspace Declutter

This phase fixes the remaining crowding inside the restaurant current-order mode.

## Changes

- The order mode no longer renders the table map beside the order workspace. Table selection is handled by the dedicated Tables mode.
- The order workspace now owns the full page width.
- The financial summary is reduced to the three decisive operator values: total, paid, remaining.
- Discount, tax and service charge remain available through the adjustment dialog and printing, but are not permanently rendered as crowded boxes.
- The action area is simplified to primary actions: send to kitchen, payment, checkout.
- Secondary actions are moved to a `More` menu: adjust, print KOT, split bill, print receipt.
- The order grid uses a focused visible column set: row, item, quantity, price, total.
- Menu item cards are smaller and denser, and the menu area is height-capped.

## Rationale

The prior fullscreen shell solved cross-mode crowding, but the order mode itself still showed too much permanent UI. This phase makes the current order suitable for laptop/touch operator screens without removing functionality.
