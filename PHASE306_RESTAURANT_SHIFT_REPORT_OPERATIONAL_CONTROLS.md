# Phase 306 — Restaurant Shift Report & Operational Controls

## Scope

This phase closes the remaining restaurant operational gap before moving to a Cafe mode: a deterministic shift report and close-readiness control surface.

## Implemented

- Added a pure restaurant shift-report contract module.
- Added local and server repository `restaurant_shift_report(...)` methods.
- Added remote gateway, abstract gateway, service, and HTTP route support.
- Exposed the report in the restaurant analytics panel with cash/card/open-balance/close-readiness cards.
- Added operational blockers: open sessions, unpaid open sessions, active kitchen tickets, and queued print jobs.
- Kept currency values as decimal strings and avoided UI-side financial recomputation.
- Added Arabic, English, and German translation keys.

## Close-readiness rule

A restaurant shift is ready to close only when:

- There are no open sessions.
- There are no unpaid open sessions.
- There are no active kitchen tickets.
- There are no queued print jobs.

## Notes

The report is read-only. It does not close the shift or mutate financial state.
