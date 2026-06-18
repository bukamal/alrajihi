# Phase 205 — Category Governance / Workspace Hardening

This phase brings material categories into the same governance model used for warehouses, branches, finance, inventory, manufacturing, POS, and transactions.

## Key changes

- Added `category_operation_policy`.
- Added `settings_service.get_category_settings()`.
- Added category RBAC actions: `categories.view/create/edit/archive/restore`.
- Routed `ProductService` category operations through the policy.
- Hardened `CategoriesWidget` operation buttons and source-row selection.
- Hardened `CategoryEditorTab` read-only behavior.
- Kept old inline category dialog as fallback only.
