# Phase 396 — Restaurant Item Card Surface

## Purpose
Unify the visual grammar of the simple restaurant POS item browser with the category browser. Menu items are now rendered as full-width rectangular cards in a single vertical column, matching category cards instead of using responsive multi-column tiles.

## Runtime behavior
- Category cards remain one vertical card per row.
- Item cards now follow the same pattern: one rectangular card per row.
- Clicking an item still adds it to the current restaurant POS invoice.
- Existing simple invoice columns remain unchanged: item name, quantity, price, total and notes.
- Resize events no longer rebuild the item grid for column-count recalculation.

## Guardrails
- `tools/phase396_restaurant_item_card_surface_guard.py`
- `tests/test_phase396_restaurant_item_card_surface.py`
- `alrajhi_client/workspace/quality/restaurant_item_card_surface_contract.py`
