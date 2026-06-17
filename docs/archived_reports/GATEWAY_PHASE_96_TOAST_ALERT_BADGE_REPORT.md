# GATEWAY PHASE 96 – Toast Positioning & Notification Badge

## Scope
- Centralized transient toast notifications in one professional fixed location.
- Added numeric badge support to the notifications button.
- Kept theme and notification buttons icon-only, with translated tooltips only.

## Changes
- `alrajhi_client/views/widgets/toast_notification.py`
  - Toasts now anchor to the main application window.
  - Toasts use top-center positioning with controlled stacking.
  - Multiple messages no longer appear at random widget positions.

- `alrajhi_client/utils.py`
  - Non-blocking message box routing still uses `show_toast()`.
  - Toast reference management is centralized inside the toast widget.

- `alrajhi_client/views/modern_topbar.py`
  - Added `alert_badge` label on top of the notification icon.
  - Added `set_alert_badge(count)`.
  - Notification button remains icon-only.

- `alrajhi_client/views/main_window.py`
  - `update_badges()` now reads `alert_service.dashboard_alerts()` and updates the notification badge.
  - Notification tooltip includes the count when alerts exist.

## Tests
- `python3 -m compileall -q alrajhi_client`
- `python3 tools/verify_phase96_toast_alert_badge.py`

## Notes
- The badge reflects current dashboard alerts from `alert_service`.
- Toasts are display-only; business logic for save/server/start/stop is unchanged.
