# Phase 444 — Lazy Page Runtime Packaging Hardening

## Purpose

Phase 436 made heavy workspaces lazy-loaded to reduce the delay after login. Phase 443 fixed source/runtime import paths. Phase 444 closes the Windows packaging gap: every lazy-loaded page factory must be available inside the PyInstaller executable, not only in the source tree.

## What changed

- Added package collection for:
  - `alrajhi_client.views`
  - `alrajhi_client.views.widgets`
  - `alrajhi_client.views.dialogs`
  - `alrajhi_client.views.restaurant`
  - `alrajhi_client.views.cafe`
  - `alrajhi_client.views.apparel`
- Added explicit hidden imports for critical lazy factories such as POS, restaurant, cafe, apparel, reports, settings, inventory, invoices, and returns.
- Added a Qt-free packaging audit that parses `PAGE_FACTORY_SPECS` and verifies that each lazy page module is either explicitly hidden-imported or covered by a collected submodule package.
- Added output matrices under `tools/audit_outputs/`.

## Files added

- `alrajhi_client/workspace/quality/lazy_page_runtime_packaging_contract.py`
- `alrajhi_client/workspace/quality/lazy_page_runtime_packaging_audit.py`
- `tools/phase444_lazy_page_runtime_packaging_guard.py`
- `tests/test_phase444_lazy_page_runtime_packaging.py`

## Files updated

- `build/pyinstaller_hidden_imports.py`
- `build/build_windows.ps1`

## Runtime implication

This phase does not change UI logic. It prevents Windows EXE regressions where a lazy page works in Python but fails in the packaged application because PyInstaller did not retain the module.
