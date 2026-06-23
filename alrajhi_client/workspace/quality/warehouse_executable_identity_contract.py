# -*- coding: utf-8 -*-
"""Phase 370 contract: Warehouse installer identity end-to-end.

The Windows release must not merely upload a Warehouse-named artifact while
building a generic Accounting executable.  PyInstaller, Inno Setup, workflow
artifact upload, and printing runtime staging must all use the Warehouse release
identity end-to-end.  This contract is PyQt-free and safe for CI/release gates.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]
PHASE = 370

BUILD_PATH = "build/build_windows.ps1"
SETUP_PATH = "build/setup.iss"
WORKFLOW_PATH = ".github/workflows/build-windows-installer.yml"
PRINTING_SERVICE_PATH = "alrajhi_client/printing/printing_service.py"
TEMPLATE_LOADER_PATH = "alrajhi_client/printing/_template_loader.py"

WAREHOUSE_REQUIRED_BUILD_TOKENS = (
    '$PyInstallerAppName = "AlrajhiAccountingWarehouse"',
    '$SetupOutputBase = "AlrajhiAccountingWarehouse_Release_Setup"',
    '$ExpectedExe = "$PyInstallerAppName.exe"',
    '--name $PyInstallerAppName',
    'Join-Path $PyInstallerDistDir "printing\\print_templates.py"',
    'Join-Path $PyInstallerDistDir "_internal\\printing\\print_templates.py"',
    'Join-Path $PyInstallerDistDir "alrajhi_client\\printing\\print_templates.py"',
    'Join-Path $PyInstallerDistDir "_internal\\alrajhi_client\\printing\\print_templates.py"',
)

WAREHOUSE_REQUIRED_SETUP_TOKENS = (
    '#define MyAppName "Alrajhi Accounting Warehouse"',
    '#define MyAppExeName "AlrajhiAccountingWarehouse.exe"',
    'DefaultDirName={autopf}\\AlrajhiAccountingWarehouse',
    'OutputBaseFilename=AlrajhiAccountingWarehouse_Release_Setup',
    'Source: "..\\dist\\AlrajhiAccountingWarehouse\\*"',
    'Filename: "{app}\\{#MyAppExeName}"',
)

WAREHOUSE_REQUIRED_WORKFLOW_TOKENS = (
    'name: AlrajhiAccountingWarehouse_Release_Installer',
    'path: output/AlrajhiAccountingWarehouse_Release_Setup.exe',
)

FORBIDDEN_BUILD_SETUP_WORKFLOW_TOKENS = (
    'AlrajhiAccounting_Release_Installer',
    'AlrajhiAccounting_Release_Portable',
    'AlrajhiAccountingWarehouse_Release_Portable',
    'AlrajhiAccounting_Release_Setup.exe',
    'OutputBaseFilename=AlrajhiAccounting_Release_Setup',
    '#define MyAppExeName "AlrajhiAccounting.exe"',
    'Source: "..\\dist\\AlrajhiAccounting\\*"',
    '--name AlrajhiAccounting',
    '$PyInstallerAppName = "AlrajhiAccounting"',
)

PRINTING_LOADER_RUNTIME_TOKENS = (
    'executable_dir = os.path.dirname(getattr(sys, "executable", "") or "")',
    'os.path.join(executable_dir, "_internal") if executable_dir else ""',
    'os.path.join(frozen_root, "_internal") if frozen_root else ""',
)


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8", errors="replace")


def _row(key: str, category: str, ok: bool, detail: object) -> Dict[str, object]:
    return {
        "key": key,
        "category": category,
        "description": key.replace("_", " "),
        "status": "pass" if ok else "fail",
        "detail": detail,
        "phase": PHASE,
    }


def warehouse_executable_identity_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    build = _read(BUILD_PATH, base)
    setup = _read(SETUP_PATH, base)
    workflow = _read(WORKFLOW_PATH, base)
    service = _read(PRINTING_SERVICE_PATH, base)
    loader = _read(TEMPLATE_LOADER_PATH, base)
    combined_release_scripts = "\n".join([build, setup, workflow])

    rows: List[Dict[str, object]] = []
    for token in WAREHOUSE_REQUIRED_BUILD_TOKENS:
        rows.append(_row(f"build_token_{token[:42]}", "pyinstaller_warehouse_identity", token in build, token))
    for token in WAREHOUSE_REQUIRED_SETUP_TOKENS:
        rows.append(_row(f"setup_token_{token[:42]}", "installer_warehouse_identity", token in setup, token))
    for token in WAREHOUSE_REQUIRED_WORKFLOW_TOKENS:
        rows.append(_row(f"workflow_token_{token[:42]}", "artifact_warehouse_identity", token in workflow, token))

    rows.append(_row(
        "workflow_has_exactly_one_artifact_upload",
        "artifact_warehouse_identity",
        workflow.count("uses: actions/upload-artifact@v4") == 1,
        workflow.count("uses: actions/upload-artifact@v4"),
    ))

    for token in FORBIDDEN_BUILD_SETUP_WORKFLOW_TOKENS:
        rows.append(_row(f"forbidden_release_script_token_{token[:42]}", "no_generic_accounting_release", token not in combined_release_scripts, token))

    rows.append(_row(
        "build_output_cleanup_is_generic_wildcard_not_named_accounting_release",
        "no_generic_accounting_release",
        'Get-ChildItem -Path (Join-Path $Root "output") -Filter "*.exe"' in build,
        "output cleanup removes stale EXEs without publishing generic release names",
    ))

    for token in PRINTING_LOADER_RUNTIME_TOKENS:
        rows.append(_row(f"printing_service_runtime_path_{token[:34]}", "installed_printing_paths", token in service, token))
        rows.append(_row(f"template_loader_runtime_path_{token[:34]}", "installed_printing_paths", token in loader, token))

    return rows


def warehouse_executable_identity_summary(root: Path | None = None) -> Dict[str, object]:
    rows = warehouse_executable_identity_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        categories[str(row["category"])] = categories.get(str(row["category"]), 0) + 1
    return {
        "phase": PHASE,
        "checks": len(rows),
        "issues": len(issues),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "PHASE",
    "warehouse_executable_identity_matrix",
    "warehouse_executable_identity_summary",
]
