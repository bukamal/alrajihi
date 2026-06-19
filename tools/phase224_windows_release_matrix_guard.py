#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 224 Windows release matrix guard.

Ensures the Windows GitHub Actions workflow publishes both the generic Release
and the Warehouse Release variants, each as portable and installer artifacts,
and keeps project branding/assets wired into PyInstaller and Inno Setup.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "build-windows-installer.yml"

REQUIRED_ARTIFACTS = [
    "AlrajhiAccounting_Release_Installer",
    "AlrajhiAccounting_Release_Portable",
    "AlrajhiAccountingWarehouse_Release_Installer",
    "AlrajhiAccountingWarehouse_Release_Portable",
]

REQUIRED_OUTPUTS = [
    "AlrajhiAccounting_Release_Setup.exe",
    "AlrajhiAccountingWarehouse_Release_Setup.exe",
]

REQUIRED_SNIPPETS = [
    "setup_release.iss",
    "setup_warehouse_release.iss",
    "Build Release Installer",
    "Build Warehouse Release Installer",
    "OutputBaseFilename \"AlrajhiAccounting_Release_Setup\"",
    "OutputBaseFilename \"AlrajhiAccountingWarehouse_Release_Setup\"",
    "SetupIconFile={#MyIcon}",
    "UninstallDisplayIcon={app}\\AlrajhiAccounting.exe",
    "IconFilename: \"{app}\\AlrajhiAccounting.exe\"",
    "--icon",
    "alrajhi_client\\assets;assets",
    "alrajhi_client\\assets;alrajhi_client\\assets",
    "Portable build missing packaged project icon assets",
    "Portable build missing alrajhi_client project icon assets",
]

FORBIDDEN_SINGLE_OUTPUT_PATTERNS = [
    "- name: Upload Setup\n",
    "- name: Upload Portable Build\n",
    "OutputBaseFilename=الراجحي_للمحاسبة_والمستودعات_Setup",
]


def main() -> int:
    errors: list[str] = []
    if not WORKFLOW.exists():
        print(f"Missing workflow: {WORKFLOW.relative_to(ROOT)}")
        return 1

    text = WORKFLOW.read_text(encoding="utf-8", errors="replace")

    for artifact in REQUIRED_ARTIFACTS:
        if f"name: {artifact}" not in text:
            errors.append(f"Missing upload artifact: {artifact}")

    for output in REQUIRED_OUTPUTS:
        if output not in text:
            errors.append(f"Missing installer output path/name: {output}")

    for snippet in REQUIRED_SNIPPETS:
        if snippet not in text:
            errors.append(f"Workflow missing required release/branding wiring: {snippet}")

    for forbidden in FORBIDDEN_SINGLE_OUTPUT_PATTERNS:
        if forbidden in text:
            errors.append(f"Legacy single-output packaging pattern is still present: {forbidden.strip()}")

    upload_count = text.count("uses: actions/upload-artifact@v4")
    if upload_count != 4:
        errors.append(f"Expected exactly 4 upload-artifact steps, found {upload_count}")

    if errors:
        print("Phase 224 Windows release matrix guard failed:")
        for err in errors:
            print(f" - {err}")
        return 1

    print("Phase 224 Windows release matrix guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
