# Phase 38 — Tabbed Workspace Shell Foundation

## Objective
Move the desktop client from one-page-at-a-time navigation toward a professional tabbed workspace while keeping the existing ERP screens stable.

## Implemented
- Added `alrajhi_client/shell/` foundation:
  - `tab_workspace.py`
  - `tab_registry.py`
  - `tab_state.py`
  - `shortcuts.py`
  - placeholder extension points for `command_bar.py` and `navigation_sidebar.py`
- Replaced `QStackedWidget` shell usage in `MainWindow` with `TabbedWorkspace`.
- Kept a compatibility alias `self.stack = self.workspace` to avoid breaking legacy methods.
- Pages are now opened as singleton tabs from navigation instead of being inserted into a static stack.
- Added `Ctrl+W` to close the current tab.
- Added dirty-tab support in the workspace foundation.
- Added Arabic, German, and English translation keys for workspace prompts.
- Added tests for the tabbed shell migration.

## Design rule
The shell layer is UI-only. It does not access database, repositories, gateways, or SQL.

## Next recommended phases
1. Convert invoice dialogs into true document tabs with dirty-state/save/print contracts.
2. Add `Quick Open` command palette for invoices/items/customers/reports.
3. Add sidebar navigation and per-language RTL/LTR placement.
4. Add document tab metadata: `document_id`, `can_close`, `save`, `refresh`, `print`, `export`.
