# Phase 225 — Printing PyInstaller Hidden Import Hotfix

## Problem

The Windows packaged build failed at startup with:

```text
ModuleNotFoundError: No module named 'printing.print_templates'
```

The source tree works because the Windows build adds `alrajhi_client` to
PyInstaller's module search path. That makes `alrajhi_client/printing` available
as the top-level package `printing`. PyInstaller did not reliably collect the
`printing.print_templates` module graph, so the packaged executable could import
`printing.print_manager` / `printing.printing_service` but then fail when the
printing templates were requested.

## Changes

- Added explicit PyInstaller collection for both package names:
  - `alrajhi_client.printing`
  - `printing`
- Added explicit hidden imports for the printing module graph:
  - `printing.print_templates`
  - `printing.printing_service`
  - `printing.print_manager`
  - `printing.thermal_printer`
  - `printing.label_designer`
  - `alrajhi_client.printing.print_templates`
  - `alrajhi_client.printing.printing_service`
  - `alrajhi_client.printing.print_manager`
- Updated:
  - `.github/workflows/build-windows-installer.yml`
  - `build/build_windows.ps1`
  - `build/pyinstaller_hidden_imports.py`
  - `tools/release_packaging_guard.py`
- Converted internal printing imports in:
  - `alrajhi_client/printing/print_manager.py`
  - `alrajhi_client/printing/printing_service.py`

  from top-level imports to package-relative imports so they work whether the
  package is loaded as `printing.*` or `alrajhi_client.printing.*`.

## Guard

Added:

```text
tools/phase225_printing_pyinstaller_guard.py
```

The guard verifies that the Windows workflow, local Windows build script, and
hidden-import manifest all include the printing package/module contract. It also
prevents internal printing modules from returning to fragile top-level template
imports.

## Validation

Executed successfully:

```text
python tools/phase225_printing_pyinstaller_guard.py
python tools/release_hidden_imports_guard.py
python tools/release_packaging_guard.py
python tools/phase224_windows_release_matrix_guard.py
python tools/phase223_finance_list_legacy_cleanup_guard.py
python tools/phase222_expense_document_shell_guard.py
python tools/phase212_runtime_stabilization_guard.py
python tools/reports_contract_check.py
python tools/advanced_runtime_test.py
python -m compileall -q alrajhi_client alrajhi_server
```

## Expected Result

The next Windows GitHub Actions build should include `printing.print_templates`
in the PyInstaller bundle and should no longer fail at startup with the reported
`ModuleNotFoundError`.
