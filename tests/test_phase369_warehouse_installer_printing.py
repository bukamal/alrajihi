# -*- coding: utf-8 -*-
"""Phase 369 warehouse installer and printing path tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.warehouse_installer_printing_contract import (  # noqa: E402
    BROWSER_OPEN_TOKENS,
    LOADER_PATH_TOKENS,
    PRINT_RUNTIME_REQUIRED_TOKENS,
    WAREHOUSE_REQUIRED_TOKENS,
    WORKFLOW_FORBIDDEN_TOKENS,
    warehouse_installer_printing_summary,
)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def test_phase369_publishes_only_warehouse_installer_artifact():
    workflow = read(".github/workflows/build-windows-installer.yml")
    setup = read("build/setup.iss")
    build = read("build/build_windows.ps1")
    combined = "\n".join([workflow, setup, build])
    assert workflow.count("uses: actions/upload-artifact@v4") == 1
    for token in WAREHOUSE_REQUIRED_TOKENS:
        assert token in combined
    for token in WORKFLOW_FORBIDDEN_TOKENS:
        assert token not in workflow


def test_phase369_build_verifies_print_runtime_files_for_installer_source():
    build = read("build/build_windows.ps1")
    for token in PRINT_RUNTIME_REQUIRED_TOKENS:
        assert token in build


def test_phase369_installed_print_template_loaders_check_executable_and_internal_paths():
    service = read("alrajhi_client/printing/printing_service.py")
    loader = read("alrajhi_client/printing/_template_loader.py")
    for token in LOADER_PATH_TOKENS:
        assert token in service
        assert token in loader


def test_phase369_browser_printing_opens_file_urls_with_qt_fallback_chain():
    service = read("alrajhi_client/printing/printing_service.py")
    for token in BROWSER_OPEN_TOKENS:
        assert token in service


def test_phase369_guard_summary_ready():
    summary = warehouse_installer_printing_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 25
