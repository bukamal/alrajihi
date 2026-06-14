# GATEWAY PHASE 95 — Return Settlement Workflow

## Scope
Implemented an explicit settlement section for Sales Returns and Purchase Returns.

## Changes
- Sales Return dialog now clearly separates:
  - calculated return value from returned quantities and original prices
  - amount actually paid now
  - settlement method
- Purchase Return dialog now clearly separates:
  - calculated return value from returned quantities and original purchase prices
  - amount actually received now
  - settlement method
- Added settlement options:
  - Credit/balance reduction only
  - Cash settlement
  - Bank settlement
- Added explanatory hint text under settlement controls.
- Cashbox is enabled only for cash settlement.
- Bank account is enabled only for bank settlement.
- Amount field is disabled and forced to zero when credit/balance reduction only is selected.
- Refund/received amount maximum is capped by calculated return total.
- Added Arabic, German, and English translations for all new labels and hints.

## Business behavior preserved
- Return value is still calculated from original invoice lines.
- Quantities are still validated against returnable quantities.
- Existing local gateway behavior remains unchanged.
- No schema migration was introduced.

## Validation
- `python3 -m compileall -q alrajhi_client`
- Translation reload check for new Phase 95 keys in Arabic/German/English.

## Notes
This phase clarifies the user workflow without changing the accounting engine. A future phase may add explicit persisted `settlement_type` if reporting needs to distinguish credit-only returns from zero-cash returns more formally.
