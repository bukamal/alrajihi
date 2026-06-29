# Phase 449 — Reports Workspace Visual Refactor

## Scope

This phase applies the central visual identity to the Reports workspace.  It does
not change report calculations, services, permissions, API gateways, printing, or
export logic.

## Problem addressed

The reports screen remained visually legacy after the shell/list/operational
migrations: the filter ribbon was a long stacked toolbar, report families and
inner reports looked like old tabs, and report result tables still used heavy
legacy headers.

## Changes

- Added report-specific design tokens in `theme/brand.py`.
- Added Phase449 central QSS rules in `theme/qss.py`.
- Tagged `ReportsWidget` with `reportsVisualPhase = 449`.
- Converted the period/filter row into a semantic `reports_filter_ribbon`.
- Tagged filter controls as `reports_filter_input`.
- Tagged refresh/print/reset as primary/secondary report actions.
- Tagged top-level report families as `reports_group_tabs`.
- Tagged inner report groups as `reports_inner_tabs`.
- Tagged all report result tables as `reports_table`.
- Tagged the report summary as `reports_summary_bar`.

## Guard

`tools/phase449_reports_workspace_visual_refactor_guard.py` verifies the tokens,
QSS markers, semantic roles, and absence of local report `setStyleSheet()`
regressions.
