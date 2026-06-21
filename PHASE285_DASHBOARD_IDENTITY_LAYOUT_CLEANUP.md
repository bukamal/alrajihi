# Phase 285 — Dashboard Identity Layout Cleanup

## Objective
Professionalize the dashboard identity area without adding new widgets, while preserving the project/developer brand card as a permanent system identity card.

## Changes
- Kept the large project/developer logo card and made its purpose explicit as **System identity**.
- Kept the company information card and made its purpose explicit as **Current company information**.
- Added a dashboard-only distinction between explicit company settings and fallback product branding.
- Added a small fallback note when company settings are not configured.
- Removed the permanent lower alerts strip from the dashboard surface.
- Preserved top-bar notifications as the correct location for alerts.
- Preserved Phase 282 removal of KPI cards and chart panels.

## Compatibility
- `_create_alerts_panel()` remains as a compatibility stub for older extension/tests.
- `_refresh_alerts()` remains as a no-op compatibility hook.
- Dashboard refresh still runs without assuming the bottom alerts table exists.

## Verification
- The dashboard no longer builds `self.alerts_panel` or adds a bottom alerts table.
- The system identity card uses product assets and does not use company settings.
- The company card uses company settings with product fallback and an explicit fallback note.
