# GATEWAY PHASE 87 – Dashboard & Items Localization Completion Hotfix

## Scope
- Dashboard UI labels and buttons.
- Dashboard company/cash/status texts.
- Items widget generic base labels.
- Item dialog remaining visible Arabic placeholder/default text.

## Changes
- Added missing translation keys for Arabic/German/English.
- Replaced remaining dashboard hardcoded visible Arabic strings with `translate(...)`.
- Added translated generic BaseWidget pagination/status/error labels used by Items.
- Replaced remaining visible item-dialog placeholders/default unit text with translation calls.

## Guard / Verification
- Verified all `translate(...)` keys used by dashboard/items/item dialog/base widget exist in ar/de/en dictionaries.
- `python3 -m compileall -q alrajhi_client` passed.

## Notes
- Internal database values such as item type codes (`مخزون`, `منتج نهائي`, `خدمة`) were intentionally preserved as internal values to avoid breaking stored data and filters.
