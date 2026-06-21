# Phase 302 — Dashboard Pixel-Style Visual Matching

This phase tightens the dashboard visual layout to more closely match the approved modern dashboard mockup while preserving the existing functional scope.

## Scope

- Keep the same three operational dashboard cards:
  - Cashbox
  - Current company information
  - Daily shortcuts
- Keep the integrated-system banner, replacing the older developer-identity wording.
- Improve spacing, card radius, banner styling, shortcut button height, company logo presentation, and cashbox balance emphasis.
- Keep exchange-rate editing inside the cashbox card and synchronized through `CurrencyManager.update_rate(...)`.
- Keep the dashboard free of the legacy KPI strip, chart panel, and bottom alerts table.

## Non-goals

- No new dashboard business widgets.
- No direct data access from the view.
- No change to invoice/POS/restaurant business workflows.
