# Phase139 - Item Movement and Invoice Profit Reports

## Scope
Continued the Reports Center implementation after Phase138-A/B.

## Added
- Item Movement report tab.
- Invoice Profitability report tab.
- Item filter in the unified report filter bar.
- Saved column layout identities through the existing CustomTableView mechanism.
- Unified print support via the existing report print pathway.
- Arabic, English, and German translation keys.

## Accounting / inventory rules
- Item movement is read from `inventory_ledger` first.
- Fallback to `inventory_movements` is kept for older databases.
- Running balance is calculated from normalized in/out direction.
- Invoice profit uses stored `invoice_lines.cost_amount`, not current item purchase price or average cost.

## Tests
- `python3 -m compileall -q alrajhi_client`
- `PYTHONPATH=alrajhi_client python3 tests/test_phase138_reporting_statements.py`

## Notes
GUI visual testing was not performed because PyQt is not available in this environment.
