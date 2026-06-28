# Phase409 — Basit Final Acceptance Audit

This phase closes the Basit-inspired visual conversion with a final static acceptance gate.

## Scope

Phase409 does not rewrite business logic. It verifies that the Basit visual system introduced in Phase401 and expanded through Phase408 is consistently registered across:

- central theme tokens and metrics,
- restaurant/POS runtime surface,
- dashboard surface,
- transaction invoices and returns,
- management/list workspaces,
- reports and settings,
- shell chrome,
- startup/login/activation/dialogs,
- browser HTML printing and thermal receipts,
- release-gate documentation, tests and guard registration.

## Output

The audit writes:

- `tools/audit_outputs/basit_final_acceptance_matrix.csv`
- `tools/audit_outputs/basit_final_acceptance_report.md`

## Acceptance rule

The project is considered visually ready for a Basit-inspired release candidate only when Phase401–Phase409 all have documentation, tests, guards, contracts and release-gate registration, and the final audit matrix has zero failures.
