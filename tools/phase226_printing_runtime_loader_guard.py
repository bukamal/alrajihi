#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 226 guard: keep printing startup safe in frozen Windows builds."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRINTING_DIR = ROOT / "alrajhi_client" / "printing"
INIT = PRINTING_DIR / "__init__.py"
LOADER = PRINTING_DIR / "_template_loader.py"
PRINT_MANAGER = PRINTING_DIR / "print_manager.py"
PRINTING_SERVICE = PRINTING_DIR / "printing_service.py"
WORKFLOW = ROOT / ".github" / "workflows" / "build-windows-installer.yml"
BUILD_PS1 = ROOT / "build" / "build_windows.ps1"
MANIFEST = ROOT / "build" / "pyinstaller_hidden_imports.py"
HOOKS = [ROOT / "build" / "hooks" / "hook-printing.py", ROOT / "build" / "hooks" / "hook-alrajhi_client.printing.py"]

REQUIRED_WORKFLOW_TOKENS = [
    '"--additional-hooks-dir", "build/hooks"',
    '"--collect-data", "printing"',
    '"--collect-data", "alrajhi_client.printing"',
    '"--hidden-import", "printing._template_loader"',
    '"--hidden-import", "alrajhi_client.printing._template_loader"',
    '"--add-data", "alrajhi_client\\printing\\print_templates.py;printing"',
    '"--add-data", "alrajhi_client\\printing\\print_templates.py;alrajhi_client\\printing"',
]

REQUIRED_BUILD_TOKENS = [
    "--additional-hooks-dir build/hooks",
    "--collect-data printing",
    "--collect-data alrajhi_client.printing",
    "--hidden-import printing._template_loader",
    "--hidden-import alrajhi_client.printing._template_loader",
    '--add-data "alrajhi_client\\printing\\print_templates.py;printing"',
    '--add-data "alrajhi_client\\printing\\print_templates.py;alrajhi_client\\printing"',
]

REQUIRED_MANIFEST_TOKENS = [
    '"printing._template_loader"',
    '"alrajhi_client.printing._template_loader"',
    "COLLECT_DATA",
]

FORBIDDEN_INIT_SNIPPETS = [
    "from .thermal_printer import",
    "from .print_manager import",
    "from .printing_service import",
    "from .label_designer import",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def main() -> int:
    errors: list[str] = []
    for path in [INIT, LOADER, PRINT_MANAGER, PRINTING_SERVICE, WORKFLOW, BUILD_PS1, MANIFEST, *HOOKS]:
        if not path.exists():
            errors.append(f"Missing required file: {path.relative_to(ROOT)}")
            continue
        if path.suffix == ".py":
            try:
                ast.parse(_read(path), filename=str(path))
            except SyntaxError as exc:
                errors.append(f"Syntax error in {path.relative_to(ROOT)}: {exc}")

    init_text = _read(INIT)
    for snippet in FORBIDDEN_INIT_SNIPPETS:
        if snippet in init_text:
            errors.append(f"printing/__init__.py is eager again: contains {snippet!r}")
    if "def __getattr__" not in init_text or "_EXPORTS" not in init_text:
        errors.append("printing/__init__.py must expose lazy __getattr__ exports")

    loader_text = _read(LOADER)
    for token in ["load_print_templates", "require_template", "printing.print_templates", "alrajhi_client.printing.print_templates"]:
        if token not in loader_text:
            errors.append(f"_template_loader.py missing token: {token}")

    service_text = _read(PRINTING_SERVICE)
    manager_text = _read(PRINT_MANAGER)
    for path, text in [(PRINT_MANAGER, manager_text), (PRINTING_SERVICE, service_text)]:
        if "from .print_templates import" in text:
            errors.append(f"{path.relative_to(ROOT)} imports print_templates directly")
    if "require_template" not in service_text or "_local_require_template" not in service_text:
        errors.append("printing_service.py must keep the late-binding template loader")
    if "from ._template_loader import require_template" in manager_text:
        errors.append("print_manager.py must not import _template_loader at module import time")
    if "from .printing_service import invoice_html" not in manager_text:
        errors.append("print_manager.py must resolve invoice_html through printing_service lazily")

    workflow = _read(WORKFLOW)
    for token in REQUIRED_WORKFLOW_TOKENS:
        if token not in workflow:
            errors.append(f"Workflow missing token: {token}")
    build = _read(BUILD_PS1)
    for token in REQUIRED_BUILD_TOKENS:
        if token not in build:
            errors.append(f"build_windows.ps1 missing token: {token}")
    manifest = _read(MANIFEST)
    for token in REQUIRED_MANIFEST_TOKENS:
        if token not in manifest:
            errors.append(f"pyinstaller_hidden_imports.py missing token: {token}")

    for hook in HOOKS:
        text = _read(hook)
        if "collect_submodules" not in text:
            errors.append(f"{hook.relative_to(ROOT)} must collect submodules")

    if errors:
        print("Phase 226 printing runtime loader guard failed:")
        for err in errors:
            print(f" - {err}")
        return 1
    print("Phase 226 printing runtime loader guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
