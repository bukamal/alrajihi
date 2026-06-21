# Phase 301 — Dashboard Professional Exchange Sync

This phase applies the approved professional dashboard layout to the uploaded Phase 300 build.

## Scope

- Preserve the three dashboard essentials: cashbox, current company information, and daily shortcuts.
- Replace the old developer/system identity wording with a clean product banner: `نظام إدارة متكامل`.
- Keep company identity separate from product identity.
- Make the cashbox card visually stronger by emphasizing the current cashbox balance.
- Add an editable exchange-rate input inside the cashbox card.
- Persist exchange-rate edits through `CurrencyManager.update_rate()` and cache them in `QSettings` so dashboard display and settings remain synchronized.
- Add Arabic, English, and German translations for the new dashboard/exchange-rate messages.

## Notes

The dashboard still does not render the old KPI strip, chart panel, or bottom alerts table.
