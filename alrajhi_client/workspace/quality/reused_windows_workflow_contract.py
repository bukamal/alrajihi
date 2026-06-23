# -*- coding: utf-8 -*-
"""Phase 371 contract: reuse the full Windows workflow while preserving Warehouse-only release identity.

The project previously used a detailed GitHub Actions workflow that performed
requirements/import validation, pyzbar DLL staging, Qt platform discovery, Inno
Setup installation, Arabic language installation, and installer compilation.
Phase 371 restores that workflow shape, but intentionally keeps the newer
Warehouse-only release policy: no generic Accounting release and no Portable
artifacts.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]
PHASE = 371
WORKFLOW_PATH = ".github/workflows/build-windows-installer.yml"
BUILD_PATH = "build/build_windows.ps1"

REQUIRED_WORKFLOW_STEPS = (
    "name: Build Windows Installer",
    "push:",
    "branches:",
    "- main",
    "- master",
    "workflow_dispatch:",
    "python-version: \"3.10\"",
    "name: Upgrade pip",
    "name: Install requirements",
    "name: Verify requirements file",
    "name: Validate imports",
    "name: Verify project structure",
    "name: Copy pyzbar DLLs",
    "name: Locate Qt platforms",
    "name: Release hardening guards",
    "name: Build executable",
    "name: Download Inno Setup",
    "name: Download Arabic Language",
    "name: Create Inno Setup Scripts",
    "name: Build Warehouse Release Installer",
    "name: Upload Warehouse Release Installer",
)

REQUIRED_WORKFLOW_WAREHOUSE_TOKENS = (
    "AlrajhiAccountingWarehouse.exe",
    "dist\\AlrajhiAccountingWarehouse\\AlrajhiAccountingWarehouse.exe",
    "dist\\AlrajhiAccountingWarehouse\\*",
    "OutputBaseFilename=AlrajhiAccountingWarehouse_Release_Setup",
    "output\\AlrajhiAccountingWarehouse_Release_Setup.exe",
    "name: AlrajhiAccountingWarehouse_Release_Installer",
    "path: output/AlrajhiAccountingWarehouse_Release_Setup.exe",
    "phase369_warehouse_installer_printing_guard.py",
    "phase370_warehouse_executable_identity_guard.py",
)

REQUIRED_PRINTING_RUNTIME_TOKENS = (
    "dist\\AlrajhiAccountingWarehouse\\printing\\print_templates.py",
    "dist\\AlrajhiAccountingWarehouse\\_internal\\printing\\print_templates.py",
    "dist\\AlrajhiAccountingWarehouse\\alrajhi_client\\printing\\print_templates.py",
    "dist\\AlrajhiAccountingWarehouse\\_internal\\alrajhi_client\\printing\\print_templates.py",
    "dist\\AlrajhiAccountingWarehouse\\printing\\_template_loader.py",
    "dist\\AlrajhiAccountingWarehouse\\_internal\\printing\\_template_loader.py",
    "dist\\AlrajhiAccountingWarehouse\\alrajhi_client\\printing\\_template_loader.py",
    "dist\\AlrajhiAccountingWarehouse\\_internal\\alrajhi_client\\printing\\_template_loader.py",
)

FORBIDDEN_WORKFLOW_TOKENS = (
    "AlrajhiAccounting_Release_Installer",
    "AlrajhiAccounting_Release_Portable",
    "AlrajhiAccountingWarehouse_Release_Portable",
    "AlrajhiAccounting_Release_Setup.exe",
    "Build Release Installer",
    "Upload Release Portable",
    "Upload Warehouse Release Portable",
    "setup_release.iss",
    "dist\\AlrajhiAccounting\\*",
    "dist\\AlrajhiAccounting\\AlrajhiAccounting.exe",
    "--name\", \"AlrajhiAccounting\"",
)

REQUIRED_BUILD_CENTRAL_TOKENS = (
    '$PyInstallerAppName = "AlrajhiAccountingWarehouse"',
    '$SetupOutputBase = "AlrajhiAccountingWarehouse_Release_Setup"',
    '--name $PyInstallerAppName',
    '$ExpectedExe = "$PyInstallerAppName.exe"',
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


def reused_windows_workflow_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    workflow = _read(WORKFLOW_PATH, base)
    build = _read(BUILD_PATH, base)
    rows: List[Dict[str, object]] = []

    for token in REQUIRED_WORKFLOW_STEPS:
        rows.append(_row(f"workflow_step_{token[:46]}", "reused_workflow_shape", token in workflow, token))

    for token in REQUIRED_WORKFLOW_WAREHOUSE_TOKENS:
        rows.append(_row(f"workflow_warehouse_{token[:46]}", "warehouse_identity", token in workflow, token))

    for token in REQUIRED_PRINTING_RUNTIME_TOKENS:
        rows.append(_row(f"workflow_printing_{token[:46]}", "printing_runtime_staging", token in workflow, token))

    for token in FORBIDDEN_WORKFLOW_TOKENS:
        rows.append(_row(f"workflow_forbidden_{token[:46]}", "no_generic_or_portable_release", token not in workflow, token))

    rows.append(_row(
        "workflow_has_exactly_one_artifact_upload",
        "no_generic_or_portable_release",
        workflow.count("uses: actions/upload-artifact@v4") == 1,
        workflow.count("uses: actions/upload-artifact@v4"),
    ))
    rows.append(_row(
        "workflow_builds_with_central_build_script",
        "warehouse_identity",
        ".\\build\\build_windows.ps1" in workflow,
        ".\\build\\build_windows.ps1",
    ))

    for token in REQUIRED_BUILD_CENTRAL_TOKENS:
        rows.append(_row(f"central_build_{token[:46]}", "warehouse_identity", token in build, token))

    return rows


def reused_windows_workflow_summary(root: Path | None = None) -> Dict[str, object]:
    rows = reused_windows_workflow_matrix(root)
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
    "reused_windows_workflow_matrix",
    "reused_windows_workflow_summary",
]
