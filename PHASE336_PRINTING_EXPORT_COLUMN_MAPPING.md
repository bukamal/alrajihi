# Phase 336 — Printing/Export Column Mapping

Phase 336 connects the universal table-column contract to official output paths.

Implemented:

- Added `workspace.tables.column_output`, a PyQt-free resolver for display, print and export columns.
- Added settings-aware keys using the pattern:
  - `ui/columns/<page>/<table>/<column>/visible`
  - `ui/columns/<page>/<table>/<column>/printable`
  - `ui/columns/<page>/<table>/<column>/exportable`
- Updated `CustomTableView` so print/export use contract output flags instead of the current hidden on-screen state.
- Updated transaction print payloads to carry `table_contract_id`/`line_table_contract_id`.
- Updated invoice/return/POS templates to build line tables from the universal contract.
- Updated restaurant receipt and kitchen-ticket templates to build line tables from restaurant/cafe contracts.
- Preserved Browser HTML as the single visible print path.

Operational result:

- Hiding a column on screen no longer necessarily removes it from print/export.
- Print/export can be controlled independently through settings.
- Apparel variants keep their variant/barcode/cost/price columns in transaction output.
- POS, restaurant and cafe output now has a shared column mapping foundation.
