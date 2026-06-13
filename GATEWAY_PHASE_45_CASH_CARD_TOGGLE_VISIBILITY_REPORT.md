# Phase 45 - Cash Card Toggle and Visibility

## Changes
- Replaced stacked daily/general movement sections inside the cash card with a single movement section.
- Added a toggle button to switch between:
  - حركة اليوم
  - الحركة العامة
- Added a small eye button in the cash card corner to hide/show balances.
- Preserved displayed currency selector.
- Preserved SYP/USD exchange-rate display.
- Kept exchange-rate editing restricted to settings/currency configuration.

## Checks
- compileall: PASS
- architecture_guard: PASS
- reports_contract_check: PASS
- phase32_invoice_flow_guard: PASS
