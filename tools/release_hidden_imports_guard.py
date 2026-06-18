#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate PyInstaller hidden imports for dynamic UI modules."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "build" / "pyinstaller_hidden_imports.py"
BUILD_FILES = [ROOT / "build" / "build_windows.ps1", ROOT / ".github" / "workflows" / "build-windows-installer.yml"]


def load_manifest() -> tuple[list[str], list[str]]:
    ns: dict[str, object] = {}
    exec(MANIFEST.read_text(encoding="utf-8"), ns)
    return list(ns.get("COLLECT_SUBMODULES", [])), list(ns.get("HIDDEN_IMPORTS", []))


def main() -> int:
    errors: list[str] = []
    if not MANIFEST.exists():
        print("Hidden imports guard failed: missing build/pyinstaller_hidden_imports.py")
        return 1
    collect, hidden = load_manifest()
    build_text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in BUILD_FILES if p.exists())

    for mod in collect:
        if f"--collect-submodules {mod}" not in build_text:
            errors.append(f"Missing --collect-submodules {mod}")
    for mod in hidden:
        if f"--hidden-import {mod}" not in build_text:
            errors.append(f"Missing --hidden-import {mod}")

    # Validate that each dynamic module exists and is syntactically parseable.
    # CI may run this guard before GUI dependencies are installed, so do not import
    # PyQt/qtawesome widgets directly here.
    for mod in hidden:
        rel = Path(*mod.split(".")).with_suffix(".py")
        candidates = [ROOT / "alrajhi_client" / rel, ROOT / rel]
        module_file = next((c for c in candidates if c.exists()), None)
        if module_file is None:
            errors.append(f"Hidden import module file missing: {mod}")
            continue
        try:
            ast.parse(module_file.read_text(encoding="utf-8"), filename=str(module_file))
        except SyntaxError as exc:
            errors.append(f"Hidden import syntax error: {mod}: {exc}")

    if errors:
        print("Release hidden imports guard failed:")
        for e in errors:
            print(f" - {e}")
        return 1
    print("Release hidden imports guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
