# Phase 167 — Return Workflow Tools

## Scope

This phase keeps the new return documents inside `TransactionDocumentTab` and adds operator-facing return workflow tools without extending the legacy dialogs.

## Added

- `features/transactions/components/transaction_return_tools.py`
  - Load returnable invoice lines.
  - Fill every return line with the remaining returnable quantity.
  - Clear entered return quantities without losing the original invoice context.
  - Show selected quantity, total returnable quantity, and selected return value.

## Changed

- `features/transactions/transaction_document_tab.py`
  - Return documents now render a dedicated return tools strip under the header.
  - Original invoice selector is editable and completion-friendly.
  - Bottom action bar includes return-specific actions:
    - `إرجاع كامل المتاح`
    - `تصفير الكميات`
  - Save validation now checks return lines through model-level base-unit validation before calling the return services.

- `features/transactions/grids/transaction_line_model.py`
  - Added `fill_return_quantities_to_max()`.
  - Added `clear_return_quantities()`.
  - Added `return_summary()`.
  - Added `return_validation_errors()` to validate quantities in base units after unit conversion.

## Architectural note

No Phase 167 logic was added to `views/dialogs/invoice_dialog.py` or the old return dialogs. The legacy screens remain fallback only.
