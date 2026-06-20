#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 57 release packaging guard.

Checks the Windows release path for files/options that historically caused
PyInstaller runtime failures: missing assets, missing build scripts, missing
critical PyInstaller collection flags, and cache artifacts in the source tree.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "requirements.txt",
    "alrajhi_client/main.py",
    "alrajhi_client/assets/brand/app.ico",
    "alrajhi_client/i18n/translator.py",
    "alrajhi_client/theme/qss.py",
    "alrajhi_client/printing/printing_service.py",
    "build/build_windows.ps1",
    ".github/workflows/build-windows-installer.yml",
    "build/pyinstaller_hidden_imports.py",
]

REQUIRED_REQUIREMENTS = [
    "PyQt5", "qt-material", "pyqtgraph", "qtawesome", "openpyxl", "reportlab",
    "qrcode", "Pillow", "python-barcode", "cryptography", "requests",
    "pyserial", "opencv-python", "pyzbar", "Flask", "Flask-JWT-Extended",
    "waitress", "Werkzeug",
]

CACHE_DIR_NAMES = {"__pycache__", ".pytest_cache"}
CACHE_PARENT_IGNORES = {".git", ".venv", "venv", "env", "dist"}

BUILD_FLAGS = [
    "--collect-all PyQt5",
    "--collect-all qtawesome",
    "--collect-all pyqtgraph",
    "--collect-submodules alrajhi_client.features",
    "--collect-submodules alrajhi_client.workspace",
    "--collect-submodules alrajhi_client.shell",
    "--collect-submodules alrajhi_client.views.restaurant",
    "--collect-submodules alrajhi_client.printing",
    "--collect-submodules printing",
    "--hidden-import printing.print_templates",
    "--hidden-import printing.printing_service",
    "--hidden-import database.connection",
    "--hidden-import database.repositories.user_repo",
    "--collect-submodules database.dao",
    "--collect-submodules database.repositories",
    "--collect-submodules database",
    "--add-data \"alrajhi_client\\assets;assets\"",
    "--add-data \"alrajhi_client\\assets;alrajhi_client\\assets\"",
]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def _is_ignored_cache_path(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    return any(part in CACHE_PARENT_IGNORES for part in rel.parts)


def _clean_generated_cache_artifacts() -> list[str]:
    """Remove Python/pytest caches created by local CI steps before release checks.

    The guard may run after compileall or pytest in CI.  Those steps create
    __pycache__/.pytest_cache directories that are not part of the source
    release payload.  Clean them first, then report only caches that could not
    be removed.
    """
    remaining: list[str] = []
    for name in CACHE_DIR_NAMES:
        for artifact in list(ROOT.rglob(name)):
            if not artifact.is_dir() or _is_ignored_cache_path(artifact):
                continue
            shutil.rmtree(artifact, ignore_errors=True)
    for name in CACHE_DIR_NAMES:
        for artifact in ROOT.rglob(name):
            if artifact.is_dir() and not _is_ignored_cache_path(artifact):
                remaining.append(str(artifact.relative_to(ROOT)))
    return sorted(set(remaining))


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            errors.append(f"Missing required release file: {rel}")

    req = read("requirements.txt") if (ROOT / "requirements.txt").exists() else ""
    for package in REQUIRED_REQUIREMENTS:
        if package not in req:
            errors.append(f"requirements.txt missing package: {package}")

    build = read("build/build_windows.ps1") if (ROOT / "build/build_windows.ps1").exists() else ""
    workflow = read(".github/workflows/build-windows-installer.yml") if (ROOT / ".github/workflows/build-windows-installer.yml").exists() else ""
    for flag in BUILD_FLAGS:
        if flag not in build and flag not in workflow:
            errors.append(f"Build path missing PyInstaller flag: {flag}")

    for artifact in _clean_generated_cache_artifacts():
        if artifact.endswith(".pytest_cache") or ".pytest_cache" in artifact:
            errors.append(f"Pytest cache artifact present after cleanup: {artifact}")
        else:
            errors.append(f"Cache artifact present after cleanup: {artifact}")

    if errors:
        print("Release packaging guard failed:")
        for e in errors:
            print(f" - {e}")
        return 1
    print("Release packaging guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
