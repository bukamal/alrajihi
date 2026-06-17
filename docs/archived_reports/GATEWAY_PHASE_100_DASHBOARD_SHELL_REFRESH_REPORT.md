# Phase 100 – Dashboard / Shell Refresh Layout

## Scope
- Dashboard layout polish.
- Shell utility buttons.
- Main navigation visual layout.

## Changes
- Removed the first dashboard hero card that appeared directly below the global search bar.
- Added a refresh button beside notification, theme, and screenshot buttons.
- Refresh button refreshes the current page when supported and updates badges.
- Reworked cashbox card order vertically:
  1. Received
  2. Paid
  3. Net
  4. Current cashbox balance
  5. Display currency
- Replaced the native text-heavy menu row with an icon-first menu bar.
- Enlarged menu icons to 32px.
- Put menu labels under icons.
- Kept the home/dashboard icon without a label as requested.

## Safety
- No database logic changed.
- No invoice, inventory, or printing logic changed.
- No server/API logic changed.

## Validation
- python -m compileall alrajhi_client: passed.
