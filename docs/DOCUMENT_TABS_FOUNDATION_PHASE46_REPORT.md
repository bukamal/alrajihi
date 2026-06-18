# Phase 46 — Document Tabs Foundation

## Scope
Converted the first high-impact modal workflows into workspace document-tab flows while preserving the existing service/gateway boundaries and unified printing path.

## Added
- `alrajhi_client/workspace/documents/base_document_tab.py`
  - `BaseDocumentTab`
  - `DocumentState`
  - `dirtyChanged`, `saved`, `titleChanged`
  - command hooks for `workspace_save`, `workspace_print`, `workspace_export`, `can_close`
- `alrajhi_client/features/items/item_editor_tab.py`
  - Item add/edit as a workspace document tab.
  - Dirty-state tracking.
  - Save through `product_service`, not database access.
- `alrajhi_client/features/categories/category_editor_tab.py`
  - Category add/edit as a workspace document tab.
  - Dirty-state tracking.
  - Save through `product_service`, not database access.

## Integrated
- `MainWindow.open_item_document()`
- `MainWindow.open_category_document()`
- `ItemsWidget.add/edit` now routes to item document tabs when hosted by `MainWindow`.
- `CategoriesWidget.add/edit` now routes to category document tabs when hosted by `MainWindow`.
- `TabbedWorkspace` now honors a tab's `can_close()` method before removing it.

## Guard
Added `tools/document_tabs_guard.py` to prevent regression to modal-only flows for the converted domains.

## Verification
- `python tools/document_tabs_guard.py` passed.
- `python tools/architecture_guard.py` passed.
- `python tools/unified_printing_guard.py` passed.
- `python tools/smart_table_rollout_guard.py` passed.
- `python tools/phase32_invoice_flow_guard.py` passed.
- `python tools/phase32_windows_import_guard.py` passed.
- `python tools/restaurant_production_readiness_guard.py` passed.
- `pytest -q`: 72 passed, 1 existing warning.
- `python -m compileall -q alrajhi_client alrajhi_server` passed.

## Next recommended phase
Phase 47 should refactor `invoice_dialog.py` into a real `InvoiceEditorTab` with components:
- `InvoiceHeader`
- `InvoiceLines`
- `InvoiceTotals`
- `InvoicePayments`
- `InvoiceToolbar`

This is the largest remaining UX/maintainability gain.
