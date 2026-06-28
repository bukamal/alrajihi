# PHASE420_API_MULTIUSER_PARITY_AUDIT_HARDENING

## Scope

Phase 420 starts the API / multi-user hardening track after the preferences registry consolidation.  The purpose is not to add new screens; it is to make the remote/local boundary, user/branch scope, offline replay and financial write metadata visible and enforceable by guards.

## Changes

- Added `alrajhi_client/workspace/quality/api_multiuser_parity_contract.py`.
- Added `alrajhi_client/workspace/quality/api_multiuser_parity_audit.py`.
- Added `tools/phase420_api_multiuser_parity_guard.py`.
- Added `tests/test_phase420_api_multiuser_parity.py`.
- Added `alrajhi_server/services/api_request_context.py` as a server-side request metadata reader.
- Hardened `alrajhi_client/database/connection_rest.py` so REST writes can carry:
  - `Idempotency-Key`
  - `X-Idempotency-Key`
  - `X-Alrajhi-Branch-Id`
  - `X-Alrajhi-Source-Branch-Id`
  - `X-Alrajhi-Target-Branch-Id`
- Hardened invoice server routes so API request context can fill missing `branch_id` before the server branch policy validates it.

## Architectural rule

The new headers are not trusted for permission decisions.  They are metadata for diagnostics, offline replay, proxy logs and future idempotency persistence.  Server-side authorization remains based on JWT identity, RBAC repository, and `ServerBranchAccessPolicy`.

## Gateway parity result

The Phase 420 guard writes:

- `tools/audit_outputs/api_multiuser_parity_matrix.csv`
- `tools/audit_outputs/api_multiuser_gateway_parity.csv`

Critical remote gateways remain required for invoices, returns, warehouse, manufacturing, restaurant, RBAC, settings and reports.

The following gateways are intentionally accepted as local-only/backlog in this phase:

- `accounting_gateway.py`
- `approval_gateway.py`
- `monitoring_gateway.py`
- `offline_queue_gateway.py`
- `system_gateway.py`
- `workflow_gateway.py`

They are not silently ignored; they are visible in the parity matrix as accepted local-only gaps.

## Multi-user / branch rules

Phase 420 confirms these server-side markers:

- JWT markers exist on API routes.
- Branch scope markers exist for branch-bound query paths.
- Branch require markers exist for branch-bound mutations.
- Permission markers exist for approval/accounting actions.
- Audit markers exist for financial/inventory mutations.

## Offline replay rules

Phase 420 keeps the existing Phase 265/270 model:

- queueable writes require conflict policy;
- queueable writes require idempotency key policy;
- offline queue duplicate collapse uses `(session_id, idempotency_key, status)`;
- replay headers carry idempotency, sync scope, conflict policy and branch id.

## Known follow-up backlog

This phase does not claim full distributed consistency yet.  The following must remain visible as follow-up phases:

1. Remote approval/workflow parity needs full endpoint implementation, not only local UI/service behavior.
2. Server-side idempotency persistence should eventually become a database-backed uniqueness rule for financial create operations.
3. Concurrent editing should be protected by optimistic locking/version columns or ETags.
4. Gateway parity should move from accepted local-only gaps to fully remote-capable implementations where the product mode requires it.

## Verification

Run:

```bash
python tools/phase420_api_multiuser_parity_guard.py
pytest tests/test_phase420_api_multiuser_parity.py -q
```

Recommended broader run:

```bash
python -m compileall alrajhi_client alrajhi_server tools tests
pytest tests/test_phase414_legacy_elimination_foundation.py tests/test_phase415_unified_sales_invoice_grid_runtime.py tests/test_phase416_runtime_acceptance_harness.py tests/test_phase417_legacy_transaction_quarantine.py tests/test_phase418_editable_grid_lifecycle_unification.py tests/test_phase419_preferences_registry_consolidation.py tests/test_phase420_api_multiuser_parity.py -q
```
