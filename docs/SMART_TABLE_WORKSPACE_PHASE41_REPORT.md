# Phase 41 — Smart Table Workspace Foundation

## Scope
This phase starts the workspace/table modernization without rewriting the full ERP UI in one risky step.

## Implemented
- Added `alrajhi_client/ui/smart_table_view.py`.
- Introduced `SmartTableView` as a backward-compatible upgrade over `CustomTableView`.
- Preserved legacy row-index behavior so existing widgets do not break after adoption.
- Added opt-in local filtering for future pages.
- Added management table identities for persistent column layouts.
- Migrated the first high-traffic management tabs:
  - Items
  - Customers
  - Suppliers

## Not Changed Intentionally
- No service/gateway data access changes.
- No full rewrite of invoice/report/settings windows.
- No forced proxy filtering on existing pages, because those pages already use service-side search and pagination.

## Verification
- Architecture guard
- Existing Phase guards
- Pytest
- Compileall
