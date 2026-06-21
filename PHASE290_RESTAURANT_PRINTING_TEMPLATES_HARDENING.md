# Phase 290 — Restaurant Printing Templates Hardening

## Scope

This phase hardens restaurant printing after the order state, KDS, and split-payment phases. It keeps all restaurant print output on the central browser-HTML printing contract and separates the three restaurant print document types:

- Customer receipt
- Kitchen order ticket (KOT)
- Internal session closing summary

## Changes

- Reworked `restaurant_receipt_html()` to format customer-visible money through the unified money display policy, include payments and split bills, and simplify the receipt columns for thermal printers.
- Reworked `restaurant_kitchen_ticket_html()` so KOT documents omit all prices, totals, taxes, and payment data. It focuses on station, table, status, waiting time, item quantity, and kitchen notes.
- Added `restaurant_session_summary_html()` for internal closing/settlement records.
- Added `restaurant_session_summary_*` methods to `PrintingService`.
- Extended `RestaurantPrintingBridge` with `session_summary_payload()` and `session_summary_print()`.
- Receipt payloads now include split-bill data when available.
- Kitchen ticket printing records a queued print job when the browser print path succeeds, preserving the printer-routing/diagnostic contract.
- Added `restaurant/session_summary_paper` to the restaurant settings contract.
- Added Arabic, English, and German translations for the new restaurant print labels.

## Guarantees

- Customer receipts include company header/logo according to print settings.
- Kitchen tickets are internal production documents and do not expose prices or payment data.
- All money values are formatted with the display currency, never raw Decimal/scientific notation.
- Browser HTML remains the only visible print path.
