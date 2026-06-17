# Phase 61 — Brand Logo, Print Direction, Dashboard Company Card

## Changes

- Company settings now use the project brand logo as the default company logo when no custom logo is set.
- HTML print templates now fall back to the project brand logo for printing.
- HTML print direction was switched from RTL to LTR to address mirrored/incorrect browser/PDF output requested by the user.
- Dashboard now has a fixed company information card between the quick-actions card and the cashbox card.
- The company information card displays:
  - Project/company logo
  - Company name
  - Address
  - Phone/email
  - Tax number
- Cashbox card and currency/exchange-rate controls were preserved.

## Guards

- `tools/phase61_brand_print_dashboard_guard.py`

## Validation

- `compileall`: PASS
- `verify_branding_assets`: PASS
- `print_action_guard`: PASS
- `html_print_expansion_guard`: PASS
- `offline_read_guard`: PASS
- `offline_widget_guard`: PASS
- `form_validation_guard`: PASS
- `manufacturing_numeric_guard`: PASS
- `phase61_brand_print_dashboard_guard`: PASS
