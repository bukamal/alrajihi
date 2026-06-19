#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 227 guard: keep lazy database repositories visible to PyInstaller."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "build/hooks/hook-database.py",
    "build/hooks/hook-database.repositories.py",
    "build/hooks/hook-database.dao.py",
    "build/hooks/hook-alrajhi_client.database.py",
]

REQUIRED_BUILD_FLAGS = [
    "--additional-hooks-dir build/hooks",
    "--collect-submodules database",
    "--collect-submodules database.repositories",
    "--collect-submodules database.dao",
    "--collect-submodules alrajhi_client.database",
    "--collect-submodules alrajhi_client.database.repositories",
    "--collect-submodules alrajhi_client.database.dao",
    "--hidden-import database.repositories.user_repo",
    "--hidden-import database.repositories.base_repo",
    "--hidden-import database.connection",
    "--hidden-import gateways.local.user_gateway",
]

REQUIRED_WORKFLOW_TOKENS = [
    '"--additional-hooks-dir", "build/hooks"',
    '"--collect-submodules", "database"',
    '"--collect-submodules", "database.repositories"',
    '"--collect-submodules", "database.dao"',
    '"--collect-submodules", "alrajhi_client.database"',
    '"--collect-submodules", "alrajhi_client.database.repositories"',
    '"--collect-submodules", "alrajhi_client.database.dao"',
    '"--hidden-import", "database.repositories.user_repo"',
    '"--hidden-import", "database.repositories.base_repo"',
    '"--hidden-import", "database.connection"',
    '"--hidden-import", "gateways.local.user_gateway"',
]

REQUIRED_MANIFEST = [
    "database",
    "database.repositories",
    "database.dao",
    "alrajhi_client.database",
    "alrajhi_client.database.repositories",
    "alrajhi_client.database.dao",
    "database.repositories.user_repo",
    "database.repositories.base_repo",
    "database.connection",
    "gateways.local.user_gateway",
]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            errors.append(f"Missing PyInstaller hook: {rel}")

    local_user_gateway = read("alrajhi_client/gateways/local/user_gateway.py")
    if "from database.repositories.user_repo import UserRepository" not in local_user_gateway:
        errors.append("Local user gateway must use direct database.repositories.user_repo import for PyInstaller login startup")
    if "from database import UserRepository" in local_user_gateway:
        errors.append("Local user gateway still uses lazy database.UserRepository import")

    build_ps1 = read("build/build_windows.ps1")
    for token in REQUIRED_BUILD_FLAGS:
        if token not in build_ps1:
            errors.append(f"build_windows.ps1 missing: {token}")

    workflow = read(".github/workflows/build-windows-installer.yml")
    for token in REQUIRED_WORKFLOW_TOKENS:
        if token not in workflow:
            errors.append(f"GitHub workflow missing: {token}")

    manifest_path = ROOT / "build" / "pyinstaller_hidden_imports.py"
    ns: dict[str, object] = {}
    exec(manifest_path.read_text(encoding="utf-8"), ns)
    manifest_values = set(ns.get("COLLECT_SUBMODULES", [])) | set(ns.get("HIDDEN_IMPORTS", []))
    for mod in REQUIRED_MANIFEST:
        if mod not in manifest_values:
            errors.append(f"pyinstaller_hidden_imports.py missing: {mod}")

    # Make sure every repository module mentioned by database.__getattr__ exists.
    db_init = ast.parse(read("alrajhi_client/database/__init__.py"))
    text = read("alrajhi_client/database/__init__.py")
    for required in ("database.repositories.user_repo", "database.repositories.settings_repo", "database.repositories.warehouse_repo"):
        if required not in text:
            errors.append(f"database lazy exports missing repository path: {required}")

    if errors:
        print("Phase 227 database PyInstaller guard failed:")
        for error in errors:
            print(f" - {error}")
        return 1
    print("Phase 227 database PyInstaller guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
