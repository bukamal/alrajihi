# -*- coding: utf-8 -*-
"""Phase 372 contract: delegated Windows workflow branding verification.

The GitHub Actions workflow intentionally delegates PyInstaller execution to
``build/build_windows.ps1``.  Branding verification must therefore inspect the
workflow, the delegated build script, and the Inno Setup script together.  This
prevents the CI from failing in the early ``Verify project structure`` step with
a false ``missing ['--icon']`` error while still enforcing real icon wiring.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]
PHASE = 372

VERIFY_PATH = "tools/verify_branding_assets.py"
WORKFLOW_PATH = ".github/workflows/build-windows-installer.yml"
BUILD_PATH = "build/build_windows.ps1"
SETUP_PATH = "build/setup.iss"

VERIFY_REQUIRED_TOKENS = (
    "BUILD_SCRIPT = ROOT / \"build\" / \"build_windows.ps1\"",
    "combined_release_wiring",
    "Workflow/build release branding wiring incomplete",
    "--icon",
)

DELEGATED_RELEASE_TOKENS = (
    ".\\build\\build_windows.ps1",
    "python tools\\verify_branding_assets.py",
    "--icon",
    "assets\\brand\\app.ico",
    "SetupIconFile",
    "IconFilename",
)

WAREHOUSE_ONLY_TOKENS = (
    "AlrajhiAccountingWarehouse.exe",
    "dist\\AlrajhiAccountingWarehouse",
    "AlrajhiAccountingWarehouse_Release_Setup",
    "AlrajhiAccountingWarehouse_Release_Installer",
)

FORBIDDEN_OUTPUT_TOKENS = (
    "AlrajhiAccounting_Release_Installer",
    "AlrajhiAccounting_Release_Portable",
    "AlrajhiAccountingWarehouse_Release_Portable",
    "output/AlrajhiAccounting_Release_Setup.exe",
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


def workflow_delegated_branding_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    verify = _read(VERIFY_PATH, base)
    workflow = _read(WORKFLOW_PATH, base)
    build = _read(BUILD_PATH, base)
    setup = _read(SETUP_PATH, base)
    combined = "\n".join([workflow, build, setup])

    rows: List[Dict[str, object]] = []
    for token in VERIFY_REQUIRED_TOKENS:
        rows.append(_row(f"verify_token_{token[:44]}", "branding_verifier", token in verify, token))

    rows.append(_row(
        "workflow_delegates_build_script",
        "workflow_shape",
        ".\\build\\build_windows.ps1" in workflow,
        ".\\build\\build_windows.ps1",
    ))
    rows.append(_row(
        "workflow_verify_step_runs_before_build",
        "workflow_shape",
        "name: Verify project structure" in workflow and "python tools\\verify_branding_assets.py" in workflow,
        "Verify project structure runs verify_branding_assets.py",
    ))

    for token in DELEGATED_RELEASE_TOKENS:
        rows.append(_row(f"combined_branding_{token[:44]}", "delegated_branding_wiring", token in combined, token))

    for token in WAREHOUSE_ONLY_TOKENS:
        rows.append(_row(f"warehouse_token_{token[:44]}", "warehouse_only_release", token in combined, token))

    for token in FORBIDDEN_OUTPUT_TOKENS:
        rows.append(_row(f"forbidden_output_{token[:44]}", "no_generic_or_portable_release", token not in workflow, token))

    return rows


def workflow_delegated_branding_summary(root: Path | None = None) -> Dict[str, object]:
    rows = workflow_delegated_branding_matrix(root)
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
    "workflow_delegated_branding_matrix",
    "workflow_delegated_branding_summary",
]
