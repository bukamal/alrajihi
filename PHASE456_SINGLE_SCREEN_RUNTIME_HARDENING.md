# Phase 456 — Single-Screen Runtime Hardening

Phase 456 hardens the screen rebuilds from Phase 455 against Windows runtime regressions.

Scope is intentionally narrow:

- Login
- Dashboard
- POS
- Invoice document editor
- Material editor

The phase is visual/layout-only. It does not change business logic, DAO/API calls, printing, permissions, persistence, inventory calculations, POS checkout logic, or Enter-grid navigation.

## Implementation

Added:

- `alrajhi_client/ui/single_screen_runtime_hardening.py`
- `alrajhi_client/workspace/quality/single_screen_runtime_hardening_contract.py`
- `tools/phase456_single_screen_runtime_hardening_guard.py`
- `tests/test_phase456_single_screen_runtime_hardening.py`

The helper applies `singleScreenRuntimeHardeningPhase = 456`, screen family markers, and a `screenRebuildGuardSignature` to the rebuilt runtime surfaces. It then locks the most important runtime hierarchy points:

- Login: compact titlebar, brand/form anchors, credential/options cards, mode chip.
- Dashboard: balanced KPI/shortcut/identity cards.
- POS: scan-first panel, major grid, payment command footer.
- Invoice editor: fast-entry card, material lookup, financial summary, sticky command footer.
- Material editor: locked cards, units grid, command footer.

## Runtime flow

The pass runs after:

1. Windows runtime visual acceptance — Phase 453.
2. Runtime layout reconstruction — Phase 454.
3. Targeted screen rebuild — Phase 455.

This ordering lets Phase 456 act as a hardening/locking pass, not a competing style layer.

## Acceptance

Expected outcome after testing Windows runtime screenshots:

- No return to native Windows-looking controls in the five targeted screens.
- POS scan/payment zones remain visually dominant.
- Invoice editor keeps the header/entry/grid/summary/footer hierarchy.
- Material editor remains card-based rather than visually fragmented.
- Login remains compact and brand/form balanced.
