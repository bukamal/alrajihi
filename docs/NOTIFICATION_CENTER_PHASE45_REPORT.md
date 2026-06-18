# Phase 45 — Notification Center

## Scope
- Added a reusable shell-level `NotificationCenter`.
- Replaced the transient alert menu with a dock-like notification drawer.
- Added `notify_user()` for non-blocking shell feedback.
- Kept notifications UI-only: no SQL, no data access, no printing logic.

## Printing Boundary
This phase does not alter unified printing. `UnifiedActionBar` and existing print
commands remain the only shell-level print entry points.

## Files
- `alrajhi_client/shell/notification_center.py`
- `alrajhi_client/views/main_window.py`
- `tools/notification_center_guard.py`
- `tests/test_phase45_notification_center.py`
