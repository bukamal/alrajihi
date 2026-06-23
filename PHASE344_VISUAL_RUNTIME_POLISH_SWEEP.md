# Phase 344 — Visual Runtime Polish Sweep

This phase applies the design-system work from Phases 331–343 at runtime.  It
adds a safe visual pass for legacy and modern workspaces without touching
business logic, repositories, printing paths, or data models.

## Scope

- Adds a PyQt-free visual policy contract for every registered workspace page.
- Covers dashboard, document, list, operational, matrix, report and settings
  workspaces.
- Applies dynamic `visualWorkspaceType` and `visualRole` properties at runtime.
- Normalizes table row density, alternating rows, header alignment, input
  heights, button roles, spacing and card roles.
- Adds global QSS selectors for the runtime visual properties.
- Hooks the pass into page switching and document-tab creation.
- Adds a guard that verifies runtime wiring and QSS coverage.

## Non-goals

This phase does not alter services, gateways, database queries, invoice posting,
restaurant/cafe operations, apparel stock logic, or HTML print output.  It is a
visual and shell consistency sweep only.
