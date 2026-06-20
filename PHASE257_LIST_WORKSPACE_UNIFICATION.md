# PHASE257_LIST_WORKSPACE_UNIFICATION

## Purpose
Unify list/grid workspaces as first-class contracts rather than scattered widget-specific tables.

This phase does not force every list to have the same visual layout. It establishes a canonical `ListWorkspaceDescriptor` for each major list surface so search, filters, columns, opening documents, permissions, print/export, API/network status, language scope, settings scope, money policy, branch policy, and audit scope are declared in one inspectable place.

## Added

- `alrajhi_client/workspace/lists/list_workspace_contract.py`
- `alrajhi_client/workspace/lists/__init__.py`
- `tools/list_workspace_contract_audit.py`
- `tests/test_phase257_list_workspace_unification.py`

## Covered list workspaces

- Sales invoices
- Purchase invoices
- Sales returns
- Purchase returns
- Materials
- Categories
- Customers
- Suppliers
- Vouchers
- Cashboxes
- Warehouses
- Warehouse transfers
- Branches

## Design rules

- Lists are not edit documents. They are query/open/filter surfaces.
- Each list points back to a `DocumentDescriptor` from Phase 249.
- List actions map to document permissions:
  - `open`, `search`, `filter`, `refresh`, `columns` -> `view`
  - `create` -> `create`
  - `update` -> `update`
  - `delete` -> `delete`
  - `print` -> `print`
  - `export` -> `export`
- API/network readiness is declared explicitly; it is not inferred from widget names.
- Money-aware lists declare a currency policy and must not render raw floats.
- Branch-aware lists declare a branch policy.

## What this phase deliberately does not do

It does not rewrite every list UI. It creates the registry and permission adapter needed to progressively bind each list to the same toolbar/search/filter/column preference policy without breaking existing screens.

## Verification

- `python -m compileall alrajhi_client alrajhi_server tests`
- `python tools/list_workspace_contract_audit.py`
- `pytest tests/test_phase257_list_workspace_unification.py`
