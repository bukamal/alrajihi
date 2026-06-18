# Phase 40 — Workspace UX

## Scope
Added the first productivity layer on top of the tabbed workspace instead of converting more legacy windows mechanically.

## Added
- `QuickOpenDialog` with `Ctrl+K` for keyboard-first page opening.
- `WorkspaceStateStore` for lightweight recent tabs, favorite pages, and safe singleton session restore.
- Recent-page tracking when a workspace tab is opened.
- Default favorites: Dashboard, Restaurant, Items, Sales Invoices, Reports.
- Session persistence on close and restore on startup for singleton pages only.
- Arabic, English, and German translation keys.

## Safety decisions
- Document tabs such as unsaved invoices are not restored yet, because safe reopen-by-id support must be implemented per document type first.
- No data access was added to the shell layer.
- No SQL or repository calls are present in the new shell modules.

## Verification
- `python tools/architecture_guard.py`
- `python tools/phase32_invoice_flow_guard.py`
- `python tools/phase32_windows_import_guard.py`
- `python tools/restaurant_production_readiness_guard.py`
- `pytest -q`
- `python -m compileall -q alrajhi_client alrajhi_server tools`
