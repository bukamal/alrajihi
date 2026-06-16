# Phase130 Return Dialog Unified Print Button

## Scope
Added an in-dialog print button for sales and purchase return dialogs, connected to the project's unified HTML printing service.

## Implemented
- Sales return dialog: added Print button with menu.
- Purchase return dialog: added Print button with menu.
- Print menu actions:
  - Preview in app
  - Open HTML in browser
  - Direct print
  - Export PDF
- Print payload is built from the current dialog state before save:
  - selected invoice
  - return date
  - party name
  - warehouse
  - payment/refund state
  - return lines
  - selected unit
  - conversion factor
  - unit price
  - line total
- Uses `printing.printing_service.return_preview/return_browser/return_print/return_pdf`.
- Added Arabic, German, and English messages for empty printable return lines and draft reference.

## Guard
- `python -m compileall -q alrajhi_client` passed.

## Accounting/UX note
The print action does not save the return. It prints the current dialog draft using the same unit/price calculation used by the return validation and save path.
