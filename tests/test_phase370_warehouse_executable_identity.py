# -*- coding: utf-8 -*-
"""Phase 370 Warehouse executable identity tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.warehouse_executable_identity_contract import (  # noqa: E402
    FORBIDDEN_BUILD_SETUP_WORKFLOW_TOKENS,
    WAREHOUSE_REQUIRED_BUILD_TOKENS,
    WAREHOUSE_REQUIRED_SETUP_TOKENS,
    WAREHOUSE_REQUIRED_WORKFLOW_TOKENS,
    warehouse_executable_identity_summary,
)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def test_phase370_pyinstaller_builds_warehouse_named_exe_and_dist():
    build = read("build/build_windows.ps1")
    for token in WAREHOUSE_REQUIRED_BUILD_TOKENS:
        assert token in build
    assert 'AlrajhiAccountingWarehouse.exe' in read("build/setup.iss")


def test_phase370_inno_packages_warehouse_dist_and_runs_warehouse_exe():
    setup = read("build/setup.iss")
    for token in WAREHOUSE_REQUIRED_SETUP_TOKENS:
        assert token in setup
    assert 'Source: "..\\dist\\AlrajhiAccounting\\*"' not in setup
    assert '#define MyAppExeName "AlrajhiAccounting.exe"' not in setup


def test_phase370_workflow_uploads_only_warehouse_installer():
    workflow = read(".github/workflows/build-windows-installer.yml")
    assert workflow.count("uses: actions/upload-artifact@v4") == 1
    for token in WAREHOUSE_REQUIRED_WORKFLOW_TOKENS:
        assert token in workflow


def test_phase370_no_generic_accounting_or_portable_release_scripts():
    combined = "\n".join([
        read("build/build_windows.ps1"),
        read("build/setup.iss"),
        read(".github/workflows/build-windows-installer.yml"),
    ])
    for token in FORBIDDEN_BUILD_SETUP_WORKFLOW_TOKENS:
        assert token not in combined


def test_phase370_guard_summary_ready():
    summary = warehouse_executable_identity_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 25
