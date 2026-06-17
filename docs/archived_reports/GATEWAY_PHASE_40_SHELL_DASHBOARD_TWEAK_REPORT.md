# Phase 40 — Shell and Dashboard Layout Tweak

## Changes

- Removed the KPI card grid from the dashboard:
  - مبيعات اليوم
  - مشتريات اليوم
  - النقدية
  - صافي الربح
  - ذمم العملاء
  - ذمم الموردين
  - المصروفات
  - التشغيل
- Removed the legacy window title strip above the menu bar by hiding `title_bar` by default.
- Moved global search, notification icon, theme toggle and user identity into a compact utility strip directly below the menu bar.
- Removed page title/breadcrumb rendering from `ModernTopBar` while preserving `set_page_context()` as a compatibility no-op.
- Kept the navigation row below the utility strip.
- Fixed Settings page duplicated headers by retaining the custom settings header only and preventing `apply_modern_widget()` from injecting a second settings header.

## Files touched

- `alrajhi_client/views/widgets/dashboard_widget.py`
- `alrajhi_client/views/modern_topbar.py`
- `alrajhi_client/views/main_window.py`
- `alrajhi_client/views/widgets/settings_widget.py`

## Validation

- `python3 -m compileall -q alrajhi_client`: PASS
- `python3 tools/architecture_guard.py`: PASS
- `python3 tools/reports_contract_check.py`: PASS
- `python3 tools/phase32_invoice_flow_guard.py`: PASS
