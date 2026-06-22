# Phase 314 — Restaurant Cafe UI Decoupling Hotfix

## Goal

Make the cafe a standalone top-level workspace in the visible UI while keeping
its audited backend behavior on the shared restaurant engine.

## Changes

- Removed the visible cafe mode entry from the restaurant operation header.
- Kept the cafe widget and mode methods for the standalone `CafeWorkspaceWidget`
  only.
- Guarded cafe actions so they return immediately when invoked from the regular
  restaurant workspace.
- Kept cafe visibility controlled by `cafe/enabled` through the top-level
  navigation/module visibility policy.
- Preserved the shared restaurant engine for cafe orders, payments, printing,
  inventory, recipes, reporting, currency, and RBAC aliases.

## Acceptance

- Restaurant workspace exposes only restaurant modes: order, kitchen, tables,
  analytics.
- Cafe workspace remains available as a top-level page when `cafe/enabled` is
  true.
- Cafe does not introduce a separate gateway, repository, payment service, or
  printing service.
