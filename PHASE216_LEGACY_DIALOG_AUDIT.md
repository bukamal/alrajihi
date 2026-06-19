# Phase 216 — Legacy Dialog Audit / Dashboard Quick Actions

## Goal
Stop dashboard quick actions from reopening large legacy dialogs after those
workflows have been migrated to workspace document tabs.

## Changes
- Dashboard invoice shortcuts now call `MainWindow.open_quick_invoice()` instead of instantiating `InvoiceDialog`.
- Dashboard customer/supplier shortcuts now call `MainWindow.open_party_document()` instead of instantiating `AddEntityDialog`.
- Added `cannot_open_document_tab` translation in Arabic, German, and English.
- Added `tools/phase216_legacy_dialog_audit_guard.py` to prevent the dashboard from regressing to legacy document dialogs.

## Policy
Small utility dialogs are still allowed where they are modal by nature, such as:
login, activation, camera barcode scan, column chooser, password change, and batch printing.

Large document/CRUD dialogs must be treated as one of:
- converted document tabs,
- explicit legacy fallback only,
- or pending migration from the legacy-dialog audit.

## Guard
Run:

```bash
python tools/phase216_legacy_dialog_audit_guard.py
```
