# PHASE 244 — Browser HTML Print Template Visual Professionalization

## Scope

This phase improves the existing browser HTML print template without changing the
network/API settings contract introduced in phases 241–243.

## Changes

- Removed the duplicated visible document title from all invoice, return,
  voucher, restaurant, manufacturing, inventory and report templates.
- Kept a single document title in the header badge (`document-badge`).
- Reworked the A4 browser view as a professional sheet with screen background,
  page padding, print-safe media CSS and no Qt print dependency.
- Reworked totals alignment so totals stay on the correct side for RTL and LTR
  documents.
- Removed the dashed empty logo placeholder when the logo is disabled or absent.
- Improved thermal output so 58/80mm receipts stay compact and do not inherit the
  desktop sheet shadow.
- Preserved SettingsService/SettingsGateway usage for company data, language,
  direction, paper size, accent color and visibility flags.

## Network and multi-user note

No local-only QSettings dependency was added. The print template still reads
through SettingsService where available, so settings profiles and remote API mode
remain the authoritative path.

## Verification

- `python -m compileall alrajhi_client alrajhi_server tests`
- `pytest -q tests/test_phase241_printing_company_settings_network_i18n.py tests/test_phase242_browser_html_print_unification_i18n.py tests/test_phase243_print_settings_ui_contract_verification.py tests/test_phase244_print_template_visual_contract.py`
