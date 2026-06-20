# PHASE277_RELEASE_READINESS_GATE

Adds a project-wide release readiness gate on top of the existing contracts.

Baseline: Phase 276 remains the active functional baseline, including grouped
settings navigation, reports grouping, report table currency formatting, and
browser-HTML report printing.

What this phase adds:

- `workspace/quality/release_gate_contract.py` as the central release gate contract.
- `tools/release_readiness_gate_audit.py` to generate a release readiness matrix.
- `tools/audit_outputs/release_readiness_gate_matrix.csv`.
- `tools/audit_outputs/release_readiness_gate_summary.json`.
- Settings diagnostics now include a Release Gate row.

The gate checks that the governance layers are still present before continuing:

- Document Shell
- Report Shell
- List Workspace
- Operational Shell
- Settings Contract
- RBAC Contract
- Branch Scope
- Audit Trail
- Offline Sync
- Offline Replay Safety
- End-to-End Scenario Guard
- Runtime Smoke Hooks
- Reports calculation/currency grouping
- Reports browser printing confirmation
- Printing/PyInstaller/browser HTML guards

This phase does not claim to run destructive business operations.  It is a
static and dry-run readiness gate intended for CI and developer diagnostics.
