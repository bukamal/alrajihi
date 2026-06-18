# Phase 44 — Dashboard Modernization

## Scope
- Added reusable dashboard UI components under `alrajhi_client/ui/dashboard_components.py`.
- Restored a modern KPI row without returning to legacy dashboard logic.
- Added a `pyqtgraph`-backed monthly trend panel with a safe fallback when the GUI/chart package is unavailable.
- Kept dashboard rendering behind `DashboardService`; no direct data access was introduced.
- Preserved unified printing boundaries: dashboard components do not print directly.

## New guard
- `tools/dashboard_modernization_guard.py`

## Notes
This phase improves the shell/dashboard experience while keeping the workspace/action-bar and unified printing architecture intact.
