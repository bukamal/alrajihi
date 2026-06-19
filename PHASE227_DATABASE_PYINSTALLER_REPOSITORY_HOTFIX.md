# Phase 227 — Database PyInstaller Repository Hotfix

## Problem

The Windows PyInstaller build crashed during login with:

```text
ModuleNotFoundError: No module named 'database.repositories.user_repo'
```

The application runs with `--paths alrajhi_client`, so `alrajhi_client/database` is imported as the top-level package `database`.  The package intentionally exposes repositories lazily through `database.__getattr__`.  PyInstaller does not reliably discover modules loaded only through lazy `import_module(...)` calls, so the generated executable omitted `database.repositories.user_repo`.

## Fix

- Changed `alrajhi_client/gateways/local/user_gateway.py` to import `UserRepository` directly from `database.repositories.user_repo` instead of through lazy `database.UserRepository`.
- Added PyInstaller collection for both top-level and package-qualified database modules:
  - `database`
  - `database.repositories`
  - `database.dao`
  - `alrajhi_client.database`
  - `alrajhi_client.database.repositories`
  - `alrajhi_client.database.dao`
- Added explicit hidden imports for all repository and DAO modules, including `database.repositories.user_repo` and `database.repositories.base_repo`.
- Added PyInstaller hooks:
  - `build/hooks/hook-database.py`
  - `build/hooks/hook-database.repositories.py`
  - `build/hooks/hook-database.dao.py`
  - `build/hooks/hook-alrajhi_client.database.py`
- Updated `build/build_windows.ps1`, `.github/workflows/build-windows-installer.yml`, `build/pyinstaller_hidden_imports.py`, and `tools/release_packaging_guard.py`.
- Added `tools/phase227_database_pyinstaller_guard.py`.

## Validation

Executed successfully:

```bash
python tools/phase227_database_pyinstaller_guard.py
python tools/release_hidden_imports_guard.py
python tools/release_packaging_guard.py
python tools/phase226_printing_runtime_loader_guard.py
python tools/phase225_printing_pyinstaller_guard.py
python tools/phase224_windows_release_matrix_guard.py
python tools/phase212_runtime_stabilization_guard.py
python tools/reports_contract_check.py
python tools/advanced_runtime_test.py
python -m compileall -q alrajhi_client alrajhi_server
```
