# Phase 168 — Transaction Print / Export Bridge

## Goal
Move printing and PDF export for the new unified transaction documents into the `features/transactions` layer, without expanding `views/dialogs/invoice_dialog.py`.

## Scope
This phase adds a dedicated output bridge for:

- Sales invoices
- Purchase invoices
- Sales returns
- Purchase returns

The legacy dialogs remain fallback surfaces only.

## Added

```text
alrajhi_client/features/transactions/components/transaction_printing_bridge.py
```

Responsibilities:

- Build printable invoice payloads from `TransactionDocumentTab` state.
- Build printable return payloads from `TransactionDocumentTab` state.
- Call the centralized `printing.printing_service` facade.
- Keep invoice/return output independent from `InvoiceDialog`.

## Updated

```text
alrajhi_client/features/transactions/transaction_document_tab.py
```

New command methods:

```text
workspace_print()
workspace_export()
_preview_document()
_open_html_preview()
_ensure_saved_for_output()
_has_printable_lines()
```

Bottom action bar now includes:

```text
معاينة
PDF
حفظ وطباعة
```

`Ctrl+P` now prints through the new bridge instead of falling back to `BaseDocumentTab.workspace_print()`.

## Behavior

- Preview can run from the current document state if there are printable lines.
- Print/PDF require the document to be saved first when it is new or dirty.
- If the document is dirty, the user is asked to save before output.
- If save fails or validation blocks saving, print/export is stopped.
- Return print payloads include item names, barcode, unit, reason, restock, and base quantity metadata.

## Guard

```text
tools/phase168_transaction_printing_guard.py
```

The guard verifies:

- `TransactionPrintingBridge` exists.
- `TransactionDocumentTab` implements `workspace_print()` and `workspace_export()`.
- Bottom action bar exposes preview/PDF commands.
- `invoice_dialog.py` is not expanded to own the new bridge.

## Validation

Executed successfully:

```text
python tools/phase168_transaction_printing_guard.py
python -m compileall -q alrajhi_client/features/transactions
python -m compileall -q alrajhi_client
```

## Architectural note

This phase closes a major functional gap in the new transaction document engine. The new invoice/return tabs no longer rely on the legacy dialog for the workspace print/export contract.
