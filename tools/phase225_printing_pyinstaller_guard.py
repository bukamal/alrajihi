#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 225 guard: ensure PyInstaller packages the printing module graph.

The Windows one-dir build runs with ``alrajhi_client`` on PyInstaller's search
path, so modules such as ``printing.printing_service`` are imported as top-level
packages.  PyInstaller may miss ``printing.print_templates`` unless the printing
package is collected explicitly.  This guard protects that contract.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "build-windows-installer.yml"
BUILD_PS1 = ROOT / "build" / "build_windows.ps1"
MANIFEST = ROOT / "build" / "pyinstaller_hidden_imports.py"
PRINT_MANAGER = ROOT / "alrajhi_client" / "printing" / "print_manager.py"
PRINTING_SERVICE = ROOT / "alrajhi_client" / "printing" / "printing_service.py"

REQUIRED_BUILD_TOKENS = [
    "--collect-submodules alrajhi_client.printing",
    "--collect-submodules printing",
    "--hidden-import printing.print_templates",
    "--hidden-import printing.printing_service",
    "--hidden-import printing.print_manager",
]

REQUIRED_WORKFLOW_TOKENS = [
    '"--collect-submodules", "alrajhi_client.printing"',
    '"--collect-submodules", "printing"',
    '"--hidden-import", "printing.print_templates"',
    '"--hidden-import", "printing.printing_service"',
    '"--hidden-import", "printing.print_manager"',
]

REQUIRED_MANIFEST_VALUES = [
    '"alrajhi_client.printing"',
    '"printing"',
    '"printing.print_templates"',
    '"printing.printing_service"',
    '"printing.print_manager"',
]


def main() -> int:
    errors: list[str] = []
    files = [WORKFLOW, BUILD_PS1, MANIFEST, PRINT_MANAGER, PRINTING_SERVICE]
    for path in files:
        if not path.exists():
            errors.append(f"Missing required file: {path.relative_to(ROOT)}")
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path)) if path.suffix == ".py" else None
        except SyntaxError as exc:
            errors.append(f"Syntax error in {path.relative_to(ROOT)}: {exc}")

    workflow = WORKFLOW.read_text(encoding="utf-8", errors="replace") if WORKFLOW.exists() else ""
    build_ps1 = BUILD_PS1.read_text(encoding="utf-8", errors="replace") if BUILD_PS1.exists() else ""
    manifest = MANIFEST.read_text(encoding="utf-8", errors="replace") if MANIFEST.exists() else ""

    for token in REQUIRED_WORKFLOW_TOKENS:
        if token not in workflow:
            errors.append(f"Workflow missing token: {token}")
    for token in REQUIRED_BUILD_TOKENS:
        if token not in build_ps1:
            errors.append(f"build_windows.ps1 missing token: {token}")
    for token in REQUIRED_MANIFEST_VALUES:
        if token not in manifest:
            errors.append(f"Hidden import manifest missing token: {token}")

    # Internal printing modules must use relative imports so they work both as
    # ``printing.*`` and ``alrajhi_client.printing.*`` package imports.
    for rel in [PRINT_MANAGER, PRINTING_SERVICE]:
        text = rel.read_text(encoding="utf-8", errors="replace") if rel.exists() else ""
        if "from printing.print_templates" in text:
            errors.append(f"{rel.relative_to(ROOT)} uses top-level print_templates import")
        if "from printing.printing_service" in text:
            errors.append(f"{rel.relative_to(ROOT)} uses top-level printing_service import")

    if errors:
        print("Phase 225 printing PyInstaller guard failed:")
        for err in errors:
            print(f" - {err}")
        return 1
    print("Phase 225 printing PyInstaller guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
