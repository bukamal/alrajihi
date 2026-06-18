# Phase 56 — Global Search Engine

## Scope

Added a workspace-level search engine behind `core.services.global_search_service`.
The Quick Open dialog now keeps its static launcher/recent/favorites behavior and
also asks the global search service for business records while the user types.

## Search domains

- Items
- Customers
- Suppliers
- Sales and purchase invoices
- Vouchers
- BOM records
- Production orders

## Architecture

The search service uses existing application services only. It does not import
DAO/repository/database modules and does not contain SQL literals. Results are
opened through existing Document Tab entry points, so global search remains
compatible with Workspace Tabs, Dirty State, Unified Action Bar, and Unified Printing.

## Guard

`tools/global_search_guard.py` verifies parseability, the Quick Open dynamic
search hook, and the absence of SQL literals in the new search service.
