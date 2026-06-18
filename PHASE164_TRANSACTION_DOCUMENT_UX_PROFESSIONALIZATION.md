# Phase 164 — Transaction Document UX Professionalization

## Goal
Move the new invoice editor further away from the legacy `InvoiceDialog` by adding professional transaction-document UX behavior inside `features/transactions` only.

## Implemented

- Added named column presets for transaction line grids:
  - `compact` / عرض مضغوط
  - `cashier` / عرض كاشير
  - `accountant` / عرض محاسب
  - `warehouse` / عرض مخزن
  - `manager` / عرض مدير
- Added persistent per-document grid preferences:
  - active preset
  - visible column keys
  - header order/size state
  - auto-responsive mode
- Enhanced `TransactionLineGrid`:
  - schema-key based visibility
  - required columns remain protected
  - named preset application
  - dominant stretch behavior for item columns
- Added `TransactionTotalsPanel`:
  - invoice totals
  - paid amount
  - remaining amount
  - payment method: cash/card/bank transfer/credit
- Added `TransactionBottomActions` as a fixed command bar component.
- Updated `TransactionDocumentTab`:
  - preset selector in title bar
  - automatic compact preset below narrow width
  - reset layout action
  - separated payment panel
  - keyboard shortcuts:
    - `Ctrl+S` save
    - `Ctrl+P` print command surface
    - `Ctrl+F` focus quick item search
    - `Insert` add line
    - `Delete` remove selected line
  - stronger save validation:
    - at least one line
    - warehouse required
    - paid amount cannot exceed invoice total
    - optional confirmation when saving without customer/supplier
    - sale stock availability guard when available quantity is known
- Preserved legacy fallback and did not expand `views/dialogs/invoice_dialog.py`.

## Architectural note
The new work remains under:

```text
alrajhi_client/features/transactions/
```

The legacy invoice dialog is still present for fallback and old flows, but Phase 164 continues the migration rule: no new invoice UX features should be added to `invoice_dialog.py`.

## Next suggested phase
Phase 165 should migrate returns to `TransactionDocumentTab` by adding return schemas and return contexts, while keeping the old return dialogs as fallback until update/create flows are proven.
