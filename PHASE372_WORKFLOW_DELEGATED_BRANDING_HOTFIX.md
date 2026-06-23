# Phase 372 — Workflow Delegated Branding Hotfix

## Problem

The restored Windows GitHub Actions workflow delegates PyInstaller execution to `build/build_windows.ps1`.
The early `Verify project structure` step runs `python tools\verify_branding_assets.py` before the build step.
The verifier only inspected `.github/workflows/build-windows-installer.yml`, so it failed with:

```text
ERROR: Workflow does not wire branding completely: missing ['--icon']
```

This was a false failure because the actual PyInstaller `--icon` wiring lives in the delegated build script.

## Fix

`tools/verify_branding_assets.py` now validates branding wiring across the complete release path:

- `.github/workflows/build-windows-installer.yml`
- `build/build_windows.ps1`
- `build/setup.iss`

The verifier still enforces real icon wiring, but it no longer requires `--icon` to exist directly inside the YAML when the workflow delegates to the central build script.

## Release policy preserved

The Windows workflow remains Warehouse-only:

- output artifact: `AlrajhiAccountingWarehouse_Release_Installer`
- installer: `AlrajhiAccountingWarehouse_Release_Setup.exe`
- executable: `AlrajhiAccountingWarehouse.exe`
- no generic Accounting release artifact
- no Portable artifact

## Validation

Added:

- `alrajhi_client/workspace/quality/workflow_delegated_branding_contract.py`
- `tools/phase372_workflow_delegated_branding_guard.py`
- `tests/test_phase372_workflow_delegated_branding.py`
