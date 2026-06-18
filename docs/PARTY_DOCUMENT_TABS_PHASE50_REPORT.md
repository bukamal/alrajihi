# Phase 50 — Party Document Tabs

## Scope
Converted customers and suppliers from modal add/edit workflows into workspace document tabs.

## Added
- `features/parties/PartyEditorTab`
- `CustomerEditorTab` and `SupplierEditorTab` wrappers
- Customer/supplier add/edit delegation from list widgets to workspace tabs
- Party statement table inside the document tab
- Linked invoice table inside the document tab
- Workspace-compatible save/print/export commands

## Preserved
- Entity persistence remains behind `EntityService` and gateways.
- Statement data remains behind `ReportingService`.
- Invoice listing remains behind `InvoiceService`.
- Printing uses existing `SmartTableView.print_table()` / centralized table printing path.
- No direct SQL, DAO, or repository access was added to UI/features.

## Verification
- `document_tabs_phase50_guard.py` passed.
- Existing architecture, printing, restaurant, SmartTable, dashboard, notification, invoice, and return guards passed.
- `pytest`: 81 passed, 1 pre-existing warning.
- `compileall`: passed.
