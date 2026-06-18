#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 57 release packaging guard.

Checks the Windows release path for files/options that historically caused
PyInstaller runtime failures: missing assets, missing build scripts, missing
critical PyInstaller collection flags, and cache artifacts in the source tree.
"""
from __future__ import annotations

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

BUILD_FLAGS = [
    "--collect-all PyQt5",
    "--collect-all qtawesome",
    "--collect-all pyqtgraph",
    "--collect-submodules alrajhi_client.features",
    "--collect-submodules alrajhi_client.workspace",
    "--collect-submodules alrajhi_client.shell",
    "--collect-submodules alrajhi_client.views.restaurant",
    "--add-data \"alrajhi_client\\assets\\brand;assets\\brand\"",
]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


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

    for artifact in ROOT.rglob("__pycache__"):
        errors.append(f"Cache artifact present: {artifact.relative_to(ROOT)}")
    for artifact in ROOT.rglob(".pytest_cache"):
        errors.append(f"Pytest cache artifact present: {artifact.relative_to(ROOT)}")

    if errors:
        print("Release packaging guard failed:")
        for e in errors:
            print(f" - {e}")
        return 1
    print("Release packaging guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
