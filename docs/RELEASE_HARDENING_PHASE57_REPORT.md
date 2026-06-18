# Phase 57 — Release Hardening

## Scope

This phase strengthens Windows/PyInstaller release safety after the workspace, document tabs, restaurant, SmartTable, notification, and unified printing changes.

## Added guards

- `tools/release_packaging_guard.py`
  - verifies required release files, assets, requirements, PyInstaller collection flags, and absence of cache artifacts.
- `tools/release_hidden_imports_guard.py`
  - verifies dynamic workspace/document/restaurant modules are included in PyInstaller hidden import or collect-submodules paths.
- `tools/release_translations_guard.py`
  - verifies critical Arabic/German/English keys and RTL/LTR direction behavior.
- `tools/release_theme_guard.py`
  - verifies theme token availability and QSS generation for the modern workspace UI.
- `tools/release_hardening_guard.py`
  - aggregate guard for all Phase 57 release checks.

## Build updates

Updated:

- `build/build_windows.ps1`
- `.github/workflows/build-windows-installer.yml`
- `build/pyinstaller_hidden_imports.py`

The build now explicitly collects/imports the dynamic packages used by:

- Workspace tabs
- Document tabs
- Restaurant UI/KDS/analytics
- Feature-based editor tabs
- Unified shell components

## Translation stability

Added stable critical keys for:

- workspace quick open/recent/favorites
- restaurant dashboard/KDS
- manufacturing label

These are re-applied when `load_translations()` reloads dictionaries so release checks do not pass only before runtime reload.

## Validation

Passed:

- `release_hardening_guard`
- `architecture_guard`
- `phase32_invoice_flow_guard`
- `phase32_windows_import_guard`
- `restaurant_production_readiness_guard`
- `smart_table_rollout_guard`
- `ui_consistency_guard`
- `pytest`: 92 passed, 1 legacy collection warning
- `compileall`: passed

## Result

The project now has an explicit release safety layer for packaging, hidden imports, translations, themes, and unified printing. This reduces the likelihood of Windows runtime failures caused by PyInstaller omissions or missing UI resources.
