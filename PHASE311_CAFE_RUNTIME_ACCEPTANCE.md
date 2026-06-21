# Phase 311 — Cafe Runtime Acceptance

## Goal

Freeze the cafe workflow as a release-gated operational contract while keeping cafe implementation on the restaurant engine.

## Scope

- Cafe quick order remains visible as a tableless workflow while the engine may keep a hidden Cafe table for referential integrity.
- Cafe drink customization is line metadata: size, add-ons, and preparation notes.
- Barista send is idempotent and must not duplicate preparation tickets.
- Cafe checkout requires full payment and no active barista tickets.
- Cafe receipt/barista aliases resolve to the existing unified restaurant Browser HTML printing surface.
- Cafe shift acceptance depends on a clear shift report with no open orders, unpaid orders, active barista tickets, or queued print jobs.

## Non-goals

- No separate cafe accounting engine.
- No separate cafe printing engine.
- No cafe-specific currency formatter.
- No table-map dependency in the visible cafe workspace.
