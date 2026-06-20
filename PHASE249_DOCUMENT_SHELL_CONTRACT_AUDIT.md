# PHASE249 — Document Shell Contract Audit

## Goal

Start unifying the project by introducing a data-only, inspectable Document Shell contract before reshaping any UI.  The contract covers document tabs, report shells, and operational shells without importing PyQt.

## Why this phase comes first

The project already contains `BaseDocumentTab`, `TransactionDocumentTab`, several specialized document tabs, legacy adapters, operational POS/Restaurant widgets, and report widgets.  Changing screens one by one would keep the inconsistency hidden.  This phase defines the canonical metadata each workspace surface must declare:

- `document_type`
- shell family: document, transaction document, report shell, operational shell, list workspace
- i18n scope
- settings scope
- gateway and API resource
- network mode: local-only, remote-available, remote-required, mixed
- local/remote gateway names
- permissions for view/create/update/delete/print/export/approve/cancel
- capabilities: save/print/export/delete/approve/cancel/barcode/grid/workflow/audit/offline queue
- currency policy
- branch policy
- audit scope
- main workspace/list route

## Added files

- `alrajhi_client/workspace/documents/document_contract.py`
- `tools/document_shell_contract_audit.py`
- `tests/test_phase249_document_shell_contract_audit.py`
- `PHASE249_DOCUMENT_SHELL_CONTRACT_AUDIT.md`

## Updated files

- `alrajhi_client/workspace/documents/__init__.py`
- `alrajhi_client/workspace/documents/base_document_tab.py`
- Transaction document tabs
- Material/category/party/voucher/expense/finance/inventory/branch/manufacturing/user/settings document tabs
- Transitional legacy invoice/return adapters now expose descriptors too

## Contract coverage

The contract currently covers these groups:

- sales invoice
- purchase invoice
- sales return
- purchase return
- material
- category
- customer
- supplier
- voucher
- expense
- cashbox
- bank account
- warehouse
- warehouse transfer
- branch
- BOM
- production order
- user
- settings section
- reports shell
- POS operational shell
- restaurant operational shell

## Important architectural decision

This phase does **not** claim all screens are visually unified.  It creates the enforceable map needed for the next phases:

1. API/remote parity, especially returns update support.
2. Permission binder for all shell actions.
3. Money/Decimal display policy for grids, totals, printing, and reports.
4. Final migration of invoices/returns/materials/reports to strict shell contracts.

## Validation

The phase adds static tests that do not import PyQt and therefore run in minimal CI/build environments.
