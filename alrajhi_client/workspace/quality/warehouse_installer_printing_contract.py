# -*- coding: utf-8 -*-
"""Phase 369 contract: Warehouse-only installer and installed printing paths.

The Windows release must publish only the Warehouse installer artifact requested
by the business.  Portable and generic Accounting release uploads are not part
of this build.  The installer source must still include the browser-HTML print
runtime files and the runtime loaders must resolve templates from installed
onedir/_internal paths.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]
PHASE = 369

BUILD_PATH = "build/build_windows.ps1"
SETUP_PATH = "build/setup.iss"
WORKFLOW_PATH = ".github/workflows/build-windows-installer.yml"
PRINTING_SERVICE_PATH = "alrajhi_client/printing/printing_service.py"
TEMPLATE_LOADER_PATH = "alrajhi_client/printing/_template_loader.py"
PACKAGING_CONTRACT_PATH = "alrajhi_client/workspace/packaging/windows_packaging_gate_contract.py"

WAREHOUSE_REQUIRED_TOKENS = (
    "AlrajhiAccountingWarehouse_Release_Installer",
    "AlrajhiAccountingWarehouse_Release_Setup.exe",
    "OutputBaseFilename=AlrajhiAccountingWarehouse_Release_Setup",
    "DefaultDirName={autopf}\\AlrajhiAccountingWarehouse",
    'Source: "..\\dist\\AlrajhiAccountingWarehouse\\*"',
    '#define MyAppExeName "AlrajhiAccountingWarehouse.exe"',
    '$PyInstallerAppName = "AlrajhiAccountingWarehouse"',
)

WORKFLOW_FORBIDDEN_TOKENS = (
    "AlrajhiAccounting_Release_Installer",
    "AlrajhiAccounting_Release_Portable",
    "AlrajhiAccountingWarehouse_Release_Portable",
    "AlrajhiAccounting_Release_Setup.exe",
    "Upload Portable",
)

PRINT_RUNTIME_REQUIRED_TOKENS = (
    "Installer staging missing packaged print template files",
    "Installer staging missing packaged print template loader",
    "print_templates.py",
    "_template_loader.py",
    '$PyInstallerDistDir "printing\\print_templates.py"',
    '$PyInstallerDistDir "_internal\\printing\\print_templates.py"',
    '$PyInstallerDistDir "alrajhi_client\\printing\\print_templates.py"',
    '$PyInstallerDistDir "_internal\\alrajhi_client\\printing\\print_templates.py"',
)

LOADER_PATH_TOKENS = (
    'executable_dir = os.path.dirname(getattr(sys, "executable", "") or "")',
    'os.path.join(frozen_root, "_internal") if frozen_root else ""',
    'os.path.join(executable_dir, "_internal") if executable_dir else ""',
)

BROWSER_OPEN_TOKENS = (
    "QUrl.fromLocalFile(abs_path)",
    "QDesktopServices.openUrl(url)",
    "webbrowser.open_new_tab(url.toString())",
    'hasattr(os, "startfile")',
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


def warehouse_installer_printing_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    build = _read(BUILD_PATH, base)
    setup = _read(SETUP_PATH, base)
    workflow = _read(WORKFLOW_PATH, base)
    printing_service = _read(PRINTING_SERVICE_PATH, base)
    template_loader = _read(TEMPLATE_LOADER_PATH, base)
    packaging_contract = _read(PACKAGING_CONTRACT_PATH, base)
    combined = "\n".join([build, setup, workflow])

    rows: List[Dict[str, object]] = []
    for token in WAREHOUSE_REQUIRED_TOKENS:
        rows.append(_row(f"required_warehouse_token_{token[:36]}", "warehouse_installer", token in combined, token))

    upload_count = workflow.count("uses: actions/upload-artifact@v4")
    rows.append(_row("workflow_upload_count_is_one", "warehouse_installer", upload_count == 1, upload_count))
    rows.append(_row(
        "workflow_uploads_warehouse_installer_only",
        "warehouse_installer",
        "name: AlrajhiAccountingWarehouse_Release_Installer" in workflow and "path: output/AlrajhiAccountingWarehouse_Release_Setup.exe" in workflow,
        "warehouse installer artifact",
    ))

    for token in WORKFLOW_FORBIDDEN_TOKENS:
        rows.append(_row(f"forbidden_workflow_token_{token}", "no_portable_accounting_release", token not in workflow, token))

    for token in PRINT_RUNTIME_REQUIRED_TOKENS:
        rows.append(_row(f"print_runtime_token_{token[:40]}", "printing_packaging", token in build, token))

    for token in LOADER_PATH_TOKENS:
        rows.append(_row(f"printing_service_loader_path_{token[:28]}", "installed_print_paths", token in printing_service, token))
        rows.append(_row(f"template_loader_path_{token[:28]}", "installed_print_paths", token in template_loader, token))

    for token in BROWSER_OPEN_TOKENS:
        rows.append(_row(f"browser_open_token_{token[:40]}", "browser_printing", token in printing_service, token))

    rows.append(_row(
        "windows_packaging_gate_knows_warehouse_only",
        "packaging_gate",
        "warehouse_installer_only" in packaging_contract and "installer_print_source" in packaging_contract,
        "windows packaging gate categories",
    ))
    rows.append(_row(
        "packaging_gate_uses_installer_staging_messages",
        "packaging_gate",
        "Installer staging missing packaged print template files" in packaging_contract
        and "Installer staging missing packaged print template loader" in packaging_contract,
        "installer staging print diagnostics",
    ))
    return rows


def warehouse_installer_printing_summary(root: Path | None = None) -> Dict[str, object]:
    rows = warehouse_installer_printing_matrix(root)
    issues = [r for r in rows if r.get("status") != "pass"]
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
    "warehouse_installer_printing_matrix",
    "warehouse_installer_printing_summary",
]
