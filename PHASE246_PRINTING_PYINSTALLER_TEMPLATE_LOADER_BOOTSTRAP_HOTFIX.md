# Phase 246 — Printing PyInstaller Template Loader Bootstrap Hotfix

## Problem
A Windows frozen build could fail during application startup with:

```text
ModuleNotFoundError: No module named 'printing._template_loader'
```

The failure happened before any print button was used because `printing_service.py` and `print_manager.py` imported `_template_loader` at module import time.

## Fix
- `printing_service.py` now treats `_template_loader` as the preferred runtime, not as a startup-critical dependency.
- If `_template_loader` is missing in a frozen build, `printing_service.py` loads `print_templates.py` directly from package imports or packaged file locations.
- If neither loader nor real templates are available, startup no longer crashes; a browser HTML diagnostic document is generated when printing is attempted.
- `print_manager.py` no longer imports `_template_loader` at module import time.
- Windows build scripts now explicitly package `_template_loader.py` as data for both top-level `printing` and qualified `alrajhi_client.printing` layouts.
- PyInstaller guards now protect `_template_loader` hidden import and data packaging.

## Network / users / languages
This is a packaging hotfix only. It does not alter database/API contracts, user permissions, or language settings. The printing language remains controlled by `SettingsService` / `SettingsGateway`.
