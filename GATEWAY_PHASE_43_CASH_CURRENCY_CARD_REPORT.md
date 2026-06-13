# Phase 43 - Cash Card Currency Integration

## Changes

- Renamed the dashboard project/cash card to: الصندوق.
- Removed the project/logo header from the dashboard cash card; branding remains in login, splash, app icon, EXE and installer assets.
- Added a currency selector inside the cash card footer.
- The selector is synced with the global display currency setting through `settings_service.set_display_currency()`.
- Added read-only SYP/USD exchange-rate display: `1 USD = <SYP rate>`.
- Exchange rate is loaded through `CurrencyManager` / `CurrencyGateway`, so it follows the configured local/remote currency source.
- Dashboard cash totals refresh immediately when the displayed currency changes.

## Design decision

The dashboard does not edit exchange rates. Exchange rates remain managed from Settings/Currency configuration to avoid accidental accounting impact from the dashboard.

## Validation

- compileall: passed
- architecture_guard: passed
- reports_contract_check: passed
- phase32_invoice_flow_guard: passed
