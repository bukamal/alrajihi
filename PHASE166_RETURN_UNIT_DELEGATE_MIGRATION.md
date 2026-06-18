# Phase 166 — Return Unit Delegate Migration

This phase moves return-unit editing into the unified TransactionDocument engine.

## Implemented

- Added `TransactionUnitDelegate` for `TransactionLineGrid`.
- The `unit` column is now text-first and opens a `QComboBox` only while editing.
- `TransactionLineModel` now owns unit conversion logic.
- Unit selection updates:
  - `unit`
  - `unit_id`
  - `conversion_factor`
  - visible unit price/cost
  - display returnable quantities
  - row total
- Return rows now keep base quantity fields:
  - `original_qty_base`
  - `previous_qty_base`
  - `returnable_qty_base`
- Return payloads now include `unit_id`, `conversion_factor`, `quantity_in_base`, `reason`, and `restock`.

## Architectural rule

Legacy return dialogs remain fallback only.  New return UX must not use always-visible `QComboBox` cell widgets.
