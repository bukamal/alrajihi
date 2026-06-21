# Phase 288 — Kitchen Display System Hardening

## Scope
Hardens the restaurant Kitchen Display System (KDS) after the order state machine introduced in Phase 287.

## Changes
- Added `alrajhi_client/features/restaurant/kitchen_display_state.py` for deterministic ticket status normalization, active ticket classification, elapsed-time calculation, overdue detection, and KDS sorting.
- Local and server restaurant repositories now support `status='active'` as the default KDS filter.
- Active KDS tickets are limited to `sent`, `preparing`, and `ready`; `served` and `cancelled` are terminal and do not pollute the active kitchen queue.
- Added ticket metadata: `priority`, `preparing_at`, `ready_at`, `served_at`, `cancelled_at`.
- KDS tickets are sorted by active/closed bucket, priority, status rank, and age.
- `KitchenDisplayWidget` now includes:
  - station filter,
  - status filter,
  - counters for sent/preparing/ready/overdue,
  - elapsed-minute labels,
  - overdue marker,
  - detail metadata,
  - explicit preparing/ready/served transitions.
- Added Arabic/English/German translations for KDS hardening keys.
- Added QSS for new KDS filters/counters/detail metadata.
- Registered Phase 288 in the release readiness gate.

## Validation
- `compileall`: passed.
- Phase/restaurant tests: passed.
- Release packaging guard: passed.
- Windows runtime packaging gate: passed.
- Release readiness gate: passed.
- Phase 32 invoice/ledger guard: passed.
