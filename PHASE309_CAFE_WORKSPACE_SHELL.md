# Phase 309 — Cafe Workspace Shell

## Scope

This phase makes cafe operation visible as an operator-focused workspace while
preserving the restaurant engine as the single implementation surface.

## Changes

- Adds a cafe workspace shell above the quick-order grid.
- Adds explicit cafe actions: new quick order, preparation / Barista, and shift report.
- Keeps cafe orders free from visible table operations and table-map workflows.
- Adds cafe-specific action wording in the shared POS widget:
  - send to preparation instead of send to kitchen,
  - preparation ticket instead of kitchen ticket,
  - cafe receipt and cafe checkout labels.
- Adds a Barista context to the KDS widget.
- Adds order-type filtering for kitchen tickets so the Barista board shows cafe quick orders only.
- Extends local, remote, service, server route and repository contracts with the optional `order_type` filter.
- Keeps printing, payment, currency, inventory, recipes and shift reporting on the unified restaurant path.

## Non-goals

- No separate cafe database model.
- No separate cafe printing engine.
- No table workflow in cafe mode.
- No duplicate payment, currency, or inventory services.
