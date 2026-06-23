# -*- coding: utf-8 -*-
"""Phase 372 delegated workflow branding tests."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def test_verify_branding_assets_accepts_delegated_build_script_icon_wiring():
    result = subprocess.run(
        [sys.executable, "tools/verify_branding_assets.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    assert "OK: branding assets" in result.stdout


def test_phase372_contract_covers_workflow_and_delegated_build_script():
    from workspace.quality.workflow_delegated_branding_contract import workflow_delegated_branding_summary

    summary = workflow_delegated_branding_summary(ROOT)
    assert summary["issues"] == 0
    assert summary["checks"] >= 18


def test_workflow_remains_warehouse_only_after_branding_verifier_fix():
    workflow = (ROOT / ".github/workflows/build-windows-installer.yml").read_text(encoding="utf-8")
    build = (ROOT / "build/build_windows.ps1").read_text(encoding="utf-8")
    assert ".\\build\\build_windows.ps1" in workflow
    assert "--icon" in build
    assert "AlrajhiAccountingWarehouse_Release_Installer" in workflow
    assert "AlrajhiAccounting_Release_Installer" not in workflow
    assert "AlrajhiAccounting_Release_Portable" not in workflow
