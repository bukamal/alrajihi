# GATEWAY PHASE 66 – Table/Tab Design System Coverage

## Scope
Applied the Al Rajhi design system to tables and tab widgets across pages, dialogs, tab pages, and dynamically-created windows.

## What changed
- Added `alrajhi_client/theme/widget_polish.py` as a runtime UI-polish layer.
- Updated `ThemeManager` so the polish layer is installed whenever the global theme is applied.
- Extended `theme/qss.py` for:
  - `QTableView`, `QTableWidget`, `QTreeView`, `QTreeWidget`,
  - table items and selected rows,
  - table corner button,
  - horizontal and vertical scrollbars,
  - `QTabWidget` panes,
  - `QTabBar` normal, hover, and selected states.
- Updated legacy local style blocks in `modern_ui.py`, `settings_widget.py`, `invoice_dialog.py`, `item_dialog.py`, `invoices_widget.py`, `pos_widget.py`, `offline_queue_widget.py`, and `monitoring_widget.py` so their colors are compatible with the Al Rajhi palette instead of the previous blue/indigo/slate palette.
- Added `tools/verify_table_tab_design_system.py` to verify static coverage.

## Runtime behavior now enforced
Every table/tree widget shown by the application is polished automatically:
- alternating rows enabled,
- grid disabled,
- full-row selection,
- unified row height,
- unified header alignment,
- last-column stretch,
- hidden vertical row header by default,
- unified object names for QSS targeting.

Every tab widget shown by the application is polished automatically:
- unified tab object naming,
- scroll buttons enabled,
- consistent tab state styling from the global design system.

## Coverage audit
Files containing table/tab references: 21.

Important UI files covered by global QSS + runtime polish include:
- `views/widgets/invoices_widget.py`
- `views/widgets/warehouses_widget.py`
- `views/widgets/reports_widget.py`
- `views/widgets/settings_widget.py`
- `views/widgets/manufacturing_widget.py`
- `views/widgets/returns_widget.py`
- `views/widgets/pos_widget.py`
- `views/widgets/cashboxes_widget.py`
- `views/widgets/branches_widget.py`
- `views/dialogs/invoice_dialog.py`
- `views/dialogs/item_dialog.py`
- `views/dialogs/production_order_dialog.py`
- `views/dialogs/production_details_dialog.py`
- `views/dialogs/batch_print_dialog.py`
- `views/custom_table_view.py`

## Validation
Executed:
- `python3 -m compileall -q alrajhi_client tools`
- `python3 tools/verify_table_tab_design_system.py`
- `python3 tools/verify_design_system.py`
- `python3 tools/verify_branding_assets.py`

All checks passed.

## Limitation
This is a visual/behavior foundation pass. It does not manually redesign the internal layout of each screen. It ensures all tables and tabs inherit the design-system appearance either from global QSS or from runtime polish when widgets are created later.
