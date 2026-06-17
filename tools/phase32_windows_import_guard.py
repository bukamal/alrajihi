#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Windows/PyInstaller packaging imports for restaurant UI modules.

This guard is intentionally static: it does not import PyQt5 or runtime modules.
It verifies that restaurant dashboard imports resolve to physical .py files and
that the Windows build script declares them as PyInstaller hidden imports.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
DASHBOARD = CLIENT / "views" / "restaurant" / "restaurant_dashboard.py"
BUILD_SCRIPT = ROOT / "build" / "build_windows.ps1"

REQUIRED_MODULES = {
    "views.restaurant.restaurant_dashboard",
    "views.restaurant.table_map_widget",
    "views.restaurant.restaurant_pos_widget",
    "views.restaurant.kitchen_display_widget",
    "views.restaurant.restaurant_analytics_widget",
    "core.services.restaurant_service",
    "gateways.restaurant_gateway",
    "gateways.local.restaurant_gateway",
    "gateways.remote.restaurant_gateway",
}


def module_to_file(module: str) -> Path:
    parts = module.split(".")
    return CLIENT.joinpath(*parts).with_suffix(".py")


def main() -> int:
    errors: list[str] = []
    if not DASHBOARD.exists():
        errors.append(f"Missing dashboard file: {DASHBOARD.relative_to(ROOT)}")
    else:
        tree = ast.parse(DASHBOARD.read_text(encoding="utf-8"), filename=str(DASHBOARD))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith(("views.restaurant", "core.services.restaurant_service", "gateways.")):
                    imported.add(node.module)
        expected_imports = {
            "views.restaurant.table_map_widget",
            "views.restaurant.restaurant_pos_widget",
            "views.restaurant.kitchen_display_widget",
            "views.restaurant.restaurant_analytics_widget",
        }
        missing_imports = expected_imports - imported
        if missing_imports:
            errors.append("restaurant_dashboard.py missing expected imports: " + ", ".join(sorted(missing_imports)))

    for module in REQUIRED_MODULES:
        file_path = module_to_file(module)
        if not file_path.exists() and not (CLIENT.joinpath(*module.split(".")) / "__init__.py").exists():
            errors.append(f"PyInstaller module has no source file/package: {module}")

    if not BUILD_SCRIPT.exists():
        errors.append("Missing build/build_windows.ps1")
    else:
        build_text = BUILD_SCRIPT.read_text(encoding="utf-8")
        for module in REQUIRED_MODULES:
            if f"--hidden-import {module}" not in build_text:
                errors.append(f"Windows build missing hidden import: {module}")

    if errors:
        print("Windows restaurant import guard failed:")
        for error in errors:
            print(f" - {error}")
        return 1
    print("Windows restaurant import guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
