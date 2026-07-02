# Phase 457 — Runtime Visual Regression Gate

## Scope

Phase 457 adds a visual/runtime regression gate for the screenshot-critical screens:

- Login
- Dashboard
- POS
- Invoice editor
- Material editor

The phase is intentionally visual-only. It does not change business logic, DAO/API, printing, permissions, persistence, activation, stock/accounting calculations, or Enter-grid navigation.

## Why this phase exists

Phase 453, 454, 455 and 456 added progressively stronger runtime visual/layout correction layers. Phase 457 does not add a new visual language. It locks the chain with deterministic runtime properties and static guards so later work cannot silently bypass the Windows visual acceptance chain.

## Runtime chain

The critical visual chain is now:

1. Phase 453 — Windows Runtime Visual Acceptance
2. Phase 454 — Runtime Layout Reconstruction
3. Phase 455 — Targeted Screen Rebuild
4. Phase 456 — Single-Screen Runtime Hardening
5. Phase 457 — Runtime Visual Regression Gate

## Main additions

- `alrajhi_client/ui/runtime_visual_regression_gate.py`
- `runtimeVisualRegressionGatePhase = 457`
- `visualRegressionGuardSignature`
- `visualRegressionGateStatus`
- `visualRegressionGateFamily`
- `PHASE457_RUNTIME_VISUAL_REGRESSION_GATE.md`
- `alrajhi_client/workspace/quality/runtime_visual_regression_gate_contract.py`
- `tools/phase457_runtime_visual_regression_gate.py`
- `tests/test_phase457_runtime_visual_regression_gate.py`

## Verification target

The gate verifies and marks whether the previous visual chain is present on each runtime surface. It gives a deterministic signature that can be checked by guards and inspected during Windows runtime diagnosis.
