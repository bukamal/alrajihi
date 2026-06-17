# SETTINGS PHASE 149 — Branches Governance Hardening Report

## Scope

Phase 149 did **not** create the branch module from zero. The project already contained a working multi-branch foundation before this phase:

- `branches` table.
- `branch_id` on invoices, vouchers, expenses, warehouses, sales returns and purchase returns.
- Branch DAO / repository / gateway / service layers.
- `BranchesWidget` screen.
- branch localization strings.
- default branch bootstrap.

The implemented work therefore focused on **governance, runtime default branch control, and diagnostics**.

## Implemented changes

### 1. Default branch management

Added a service-level runtime default branch path:

- `BranchService.set_default_branch(branch_id)`
- `BranchRepository.set_default(branch_id)`
- `BranchDAO.set_default(branch_id)`
- local gateway adapter support

The selected default branch is persisted in:

- the `branches.is_default` flag
- `settings` key: `branches/default_branch_id`

`BranchService.default_branch_id()` now checks the configured setting first, validates that the branch is still active, and falls back to the repository default if the setting is invalid.

### 2. Branch UI enhancement

`BranchesWidget` now includes:

- `⭐ تعيين كفرع افتراضي`

This lets the operator select a branch from the branch table and make it the runtime/default branch.

### 3. Branch diagnostics

Added branch diagnostics through:

- `BranchRepository.branch_diagnostics()`
- `BranchDAO.diagnostics()`
- `BranchGateway.diagnostics()`
- `BranchService.diagnostics()`

Reported checks include:

- active branches count
- default branch id
- warehouses without branch
- invoices without branch
- vouchers without branch
- returns without branch

### 4. Settings diagnostics integration

The Settings diagnostics tab now shows a dedicated `الفروع` section, including:

- current/default branch name
- active branch count
- branch linkage risks

The general statistics section now also includes:

- branches count
- warehouses count

### 5. Advanced integrity checks

`SystemService.integrity_checks()` now includes branch-related operational checks:

- `branches_count`
- `warehouses_without_branch`
- `invoices_without_branch`
- `returns_without_branch`

These checks contribute to the risk count where appropriate.

## Notes

Remote/server mode includes safe stubs for default-branch switching because the current REST client exposes branch CRUD but no dedicated endpoint for changing the default branch.

## Validation

Executed:

```bash
python -m compileall -q alrajhi_client
```

Result: Python compilation passed.
