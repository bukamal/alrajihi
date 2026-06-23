#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 224/369 Windows release artifact guard.

Phase 369 intentionally supersedes the old four-artifact matrix.  The release
pipeline now publishes only the Warehouse installer artifact and does not upload
portable or generic accounting release artifacts.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "build-windows-installer.yml"
SETUP = ROOT / "build" / "setup.iss"
BUILD = ROOT / "build" / "build_windows.ps1"

REQUIRED_TOKENS = [
    "AlrajhiAccountingWarehouse_Release_Installer",
    "AlrajhiAccountingWarehouse_Release_Setup.exe",
    "AlrajhiAccountingWarehouse.exe",
    "OutputBaseFilename=AlrajhiAccountingWarehouse_Release_Setup",
    r'Source: "..\dist\AlrajhiAccountingWarehouse\*"',
    r"UninstallDisplayIcon={app}\{#MyAppExeName}",
    r'IconFilename: "{app}\{#MyAppExeName}"',
]

FORBIDDEN_TOKENS = [
    "AlrajhiAccounting_Release_Installer",
    "AlrajhiAccounting_Release_Portable",
    "AlrajhiAccountingWarehouse_Release_Portable",
    "AlrajhiAccounting_Release_Setup.exe",
    "Upload Portable",
]


def main() -> int:
    errors: list[str] = []
    workflow = WORKFLOW.read_text(encoding="utf-8", errors="replace") if WORKFLOW.exists() else ""
    setup = SETUP.read_text(encoding="utf-8", errors="replace") if SETUP.exists() else ""
    build = BUILD.read_text(encoding="utf-8", errors="replace") if BUILD.exists() else ""
    combined = "\n".join([workflow, setup, build])

    for token in REQUIRED_TOKENS:
        if token not in combined:
            errors.append(f"Missing required warehouse-installer release token: {token}")
    for token in FORBIDDEN_TOKENS:
        if token in workflow:
            errors.append(f"Forbidden portable/generic release token still in workflow: {token}")

    upload_count = workflow.count("uses: actions/upload-artifact@v4")
    if upload_count != 1:
        errors.append(f"Expected exactly 1 installer upload-artifact step, found {upload_count}")

    if errors:
        print("Warehouse-only Windows release guard failed:")
        for err in errors:
            print(f" - {err}")
        return 1
    print("Warehouse-only Windows release guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
