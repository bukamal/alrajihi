# Phase 300 — Restaurant Order Search Header & Collapsible Menu

This phase finishes the current-order restaurant workspace decluttering.

Changes:

- Moves restaurant menu/barcode search into the order header next to session/table and guest controls.
- Keeps manual item entry beside the search field for fast operator access.
- Removes the permanent bottom search strip.
- Makes the product/menu grid collapsible through a dedicated `restaurantMenuToggleButton`.
- Keeps the order table as the dominant working surface.
- Hides secondary order-grid columns by default: modifiers, unit, kitchen status, and notes. These remain available as model data/tooling details but are not permanent visual columns.
- Keeps the primary action bar visible: send to kitchen, record payment, checkout, and more.

The goal is practical: bigger table, clearer action buttons, less bottom clutter.
