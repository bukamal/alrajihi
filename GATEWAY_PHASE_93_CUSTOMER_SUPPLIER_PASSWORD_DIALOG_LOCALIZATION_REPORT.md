# Phase 93 – Customer / Supplier / Password Dialog Localization

Applied on top of Phase 92 package supplied by the user.

## Scope
- Customer add/edit dialog flow.
- Supplier add/edit dialog flow.
- Change password dialog.

## Changes
- Localized titles, labels, placeholders, save/cancel buttons, validation and password messages.
- Added Arabic/German/English translation keys.
- Applied runtime layout direction via the existing i18n direction helper.
- Kept business logic and database fields unchanged.

## Verification
- `python3 tools/verify_phase93_customer_supplier_password.py`
- `python3 -m compileall -q alrajhi_client`

## Notes
The add customer/supplier shared dialog remains a single implementation and now derives labels from translation keys.
