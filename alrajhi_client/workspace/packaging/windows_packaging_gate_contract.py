# -*- coding: utf-8 -*-
"""Windows runtime packaging gate (Phase 278).

The application has repeatedly failed in Windows one-dir builds when PyInstaller
missed late-bound modules or packaged Python template files incorrectly.  This
contract is intentionally stdlib-only and PyQt-free so it can run before a build,
inside CI, and from release diagnostics.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[3]

WINDOWS_PACKAGING_GATE_PHASE = 278


@dataclass(frozen=True)
class PackagingGateCheck:
    key: str
    category: str
    title: str
    source_path: str = ""
    build_tokens: Sequence[str] = ()
    workflow_tokens: Sequence[str] = ()
    manifest_tokens: Sequence[str] = ()
    syntax_paths: Sequence[str] = ()
    required: bool = True


REQUIRED_RUNTIME_FILES: Sequence[str] = (
    "requirements.txt",
    "alrajhi_client/main.py",
    "alrajhi_client/printing/_template_loader.py",
    "alrajhi_client/printing/print_templates.py",
    "alrajhi_client/printing/printing_service.py",
    "alrajhi_client/database/migrations.py",
    "alrajhi_server/database/migrations.py",
    "build/build_windows.ps1",
    "build/pyinstaller_hidden_imports.py",
    "build/hooks/hook-printing.py",
    "build/hooks/hook-alrajhi_client.printing.py",
    ".github/workflows/build-windows-installer.yml",
)

# Source files that are especially dangerous when shipped as data files because
# PyInstaller may not import them during analysis.  Parse them explicitly.
REQUIRED_SYNTAX_FILES: Sequence[str] = (
    "alrajhi_client/main.py",
    "alrajhi_client/printing/_template_loader.py",
    "alrajhi_client/printing/print_templates.py",
    "alrajhi_client/printing/printing_service.py",
    "alrajhi_client/database/migrations.py",
    "alrajhi_server/database/migrations.py",
    "build/pyinstaller_hidden_imports.py",
    "build/hooks/hook-printing.py",
    "build/hooks/hook-alrajhi_client.printing.py",
)

REQUIRED_HIDDEN_IMPORTS: Sequence[str] = (
    "printing._template_loader",
    "printing.print_templates",
    "printing.printing_service",
    "printing.print_manager",
    "printing.thermal_printer",
    "printing.label_designer",
    "alrajhi_client.printing._template_loader",
    "alrajhi_client.printing.print_templates",
    "alrajhi_client.printing.printing_service",
    "alrajhi_client.printing.print_manager",
    "database.migrations",
    "alrajhi_client.database.migrations",
    "database.schema_manager",
    "alrajhi_client.database.schema_manager",
    "flask_jwt_extended",
)

REQUIRED_COLLECT_SUBMODULES: Sequence[str] = (
    "alrajhi_client.printing",
    "printing",
    "alrajhi_client.database",
    "database",
    "alrajhi_client.database.repositories",
    "database.repositories",
    "alrajhi_client.database.dao",
    "database.dao",
    "alrajhi_client.workspace",
    "workspace",
    "alrajhi_client.gateways.local",
    "gateways.local",
)

REQUIRED_ADD_DATA: Sequence[str] = (
    "alrajhi_client\\printing\\_template_loader.py;printing",
    "alrajhi_client\\printing\\_template_loader.py;alrajhi_client\\printing",
    "alrajhi_client\\printing\\print_templates.py;printing",
    "alrajhi_client\\printing\\print_templates.py;alrajhi_client\\printing",
    "alrajhi_client\\assets;assets",
    "alrajhi_client\\assets;alrajhi_client\\assets",
)

REQUIRED_POST_BUILD_TOKENS: Sequence[str] = (
    "print_templates.py",
    "_template_loader.py",
    "Installer staging missing packaged print template files",
    "Installer staging missing packaged print template loader",
)

REQUIRED_GITIGNORE_BUILD_TRACKING: Sequence[str] = (
    "build/*",
    "!build/",
    "!build/build_windows.ps1",
    "!build/setup.iss",
    "!build/pyinstaller_hidden_imports.py",
    "!build/hooks/",
    "!build/hooks/*.py",
)

PACKAGING_GATE_CHECKS: Sequence[PackagingGateCheck] = (
    PackagingGateCheck("runtime_files", "files", "Required runtime files"),
    PackagingGateCheck("source_syntax", "syntax", "Runtime source syntax"),
    PackagingGateCheck("hidden_import_manifest", "pyinstaller", "Hidden import manifest coverage"),
    PackagingGateCheck("collect_submodules", "pyinstaller", "Collected submodule coverage"),
    PackagingGateCheck("printing_data_files", "pyinstaller", "Printing template data files"),
    PackagingGateCheck("hooks", "pyinstaller", "PyInstaller hooks collect Python template files"),
    PackagingGateCheck("workflow_gate", "ci", "GitHub workflow runs packaging gate"),
    PackagingGateCheck("build_ps1_gate", "build", "Local Windows build runs packaging gate"),
    PackagingGateCheck("post_build_runtime_files", "build", "Post-build packaged runtime file verification"),
    PackagingGateCheck("warehouse_installer_only", "release", "Only Warehouse installer release artifact is published"),
    PackagingGateCheck("installer_print_source", "printing", "Installer source preserves print runtime files"),
    PackagingGateCheck("gitignore_tracking", "release", "Required build contract files are trackable"),
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _parse_python_source_for_release(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    try:
        ast.parse(text, filename=str(path), feature_version=(3, 11))
    except TypeError:  # pragma: no cover - compatibility with older Python runtimes
        ast.parse(text, filename=str(path))


def _load_manifest(root: Path) -> Mapping[str, Sequence[str]]:
    manifest_path = root / "build" / "pyinstaller_hidden_imports.py"
    ns: Dict[str, object] = {}
    if manifest_path.exists():
        exec(manifest_path.read_text(encoding="utf-8"), ns)
    return {
        "HIDDEN_IMPORTS": tuple(ns.get("HIDDEN_IMPORTS", ()) or ()),
        "COLLECT_SUBMODULES": tuple(ns.get("COLLECT_SUBMODULES", ()) or ()),
        "COLLECT_DATA": tuple(ns.get("COLLECT_DATA", ()) or ()),
    }


def _module_file_for_hidden_import(root: Path, module: str) -> Path | None:
    rel = Path(*module.split(".")).with_suffix(".py")
    candidates = (root / rel, root / "alrajhi_client" / rel)
    return next((candidate for candidate in candidates if candidate.exists()), None)


def packaging_gate_checks() -> Sequence[PackagingGateCheck]:
    return PACKAGING_GATE_CHECKS


def packaging_gate_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    issues = validate_windows_packaging_gate(base)
    rows: List[Dict[str, object]] = []
    for check in PACKAGING_GATE_CHECKS:
        rows.append({
            "key": check.key,
            "category": check.category,
            "title": check.title,
            "required": check.required,
            "status": "fail" if check.key in issues else "pass",
            "issues": len(issues.get(check.key, [])),
        })
    return rows


def validate_windows_packaging_gate(root: Path | None = None) -> Dict[str, List[str]]:
    base = root or ROOT
    issues: Dict[str, List[str]] = {}

    def add(key: str, message: str) -> None:
        issues.setdefault(key, []).append(message)

    workflow_path = base / ".github" / "workflows" / "build-windows-installer.yml"
    build_path = base / "build" / "build_windows.ps1"
    manifest_path = base / "build" / "pyinstaller_hidden_imports.py"
    workflow = _read(workflow_path)
    build = _read(build_path)
    manifest_text = _read(manifest_path)
    combined_build_text = workflow + "\n" + build
    manifest = _load_manifest(base)

    for rel in REQUIRED_RUNTIME_FILES:
        if not (base / rel).exists():
            add("runtime_files", f"missing {rel}")

    gitignore_lines = {
        line.strip()
        for line in _read(base / ".gitignore").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    if "build/" in gitignore_lines and "build/*" not in gitignore_lines:
        add("gitignore_tracking", ".gitignore ignores build/ wholesale; required build files may be absent in CI")
    for pattern in REQUIRED_GITIGNORE_BUILD_TRACKING:
        if pattern not in gitignore_lines:
            add("gitignore_tracking", f".gitignore missing tracking exception {pattern}")

    for rel in REQUIRED_SYNTAX_FILES:
        path = base / rel
        if not path.exists():
            continue
        try:
            _parse_python_source_for_release(path)
        except SyntaxError as exc:
            add("source_syntax", f"syntax error in {rel}: {exc}")

    hidden = set(manifest.get("HIDDEN_IMPORTS", ()))
    collect = set(manifest.get("COLLECT_SUBMODULES", ()))
    collect_data = set(manifest.get("COLLECT_DATA", ()))

    for module in REQUIRED_HIDDEN_IMPORTS:
        if module not in hidden:
            add("hidden_import_manifest", f"manifest missing hidden import {module}")
        if f"--hidden-import {module}" not in build and f'"--hidden-import", "{module}"' not in workflow:
            add("hidden_import_manifest", f"build/workflow missing hidden import {module}")
        module_file = _module_file_for_hidden_import(base, module)
        if module_file is not None:
            try:
                _parse_python_source_for_release(module_file)
            except SyntaxError as exc:
                add("hidden_import_manifest", f"hidden import syntax error {module}: {exc}")

    for module in REQUIRED_COLLECT_SUBMODULES:
        if module not in collect:
            add("collect_submodules", f"manifest missing collect-submodules {module}")
        if f"--collect-submodules {module}" not in build and f'"--collect-submodules", "{module}"' not in workflow:
            add("collect_submodules", f"build/workflow missing collect-submodules {module}")

    for module in ("printing", "alrajhi_client.printing"):
        if module not in collect_data:
            add("printing_data_files", f"manifest missing collect-data {module}")
        if f"--collect-data {module}" not in build and f'"--collect-data", "{module}"' not in workflow:
            add("printing_data_files", f"build/workflow missing collect-data {module}")

    for token in REQUIRED_ADD_DATA:
        if token not in combined_build_text:
            add("printing_data_files", f"missing add-data token {token}")

    for rel in ("build/hooks/hook-printing.py", "build/hooks/hook-alrajhi_client.printing.py"):
        text = _read(base / rel)
        if "collect_submodules" not in text:
            add("hooks", f"{rel} must collect submodules")
        if "collect_data_files" not in text or "include_py_files=True" not in text:
            add("hooks", f"{rel} must collect template .py files with include_py_files=True")

    if "python tools\\windows_runtime_packaging_gate_audit.py" not in workflow and "python tools/windows_runtime_packaging_gate_audit.py" not in workflow:
        add("workflow_gate", "workflow must run tools/windows_runtime_packaging_gate_audit.py before build")
    if "python tools\\windows_runtime_packaging_gate_audit.py" not in build and "python tools/windows_runtime_packaging_gate_audit.py" not in build:
        add("build_ps1_gate", "build_windows.ps1 must run tools/windows_runtime_packaging_gate_audit.py")

    for token in REQUIRED_POST_BUILD_TOKENS:
        if token not in combined_build_text:
            add("post_build_runtime_files", f"missing post-build token {token}")

    required_installer_tokens = (
        "AlrajhiAccountingWarehouse_Release_Installer",
        "AlrajhiAccountingWarehouse_Release_Setup.exe",
        "OutputBaseFilename=AlrajhiAccountingWarehouse_Release_Setup",
    )
    for token in required_installer_tokens:
        if token not in combined_build_text and token not in _read(base / "build" / "setup.iss"):
            add("warehouse_installer_only", f"missing warehouse installer token {token}")
    forbidden_release_tokens = (
        "AlrajhiAccounting_Release_Installer",
        "AlrajhiAccounting_Release_Portable",
        "AlrajhiAccountingWarehouse_Release_Portable",
        "AlrajhiAccounting_Release_Setup.exe",
        "Upload Portable",
    )
    for token in forbidden_release_tokens:
        if token in workflow:
            add("warehouse_installer_only", f"workflow still publishes forbidden artifact/output {token}")

    setup_text = _read(base / "build" / "setup.iss")
    if r'Source: "..\dist\AlrajhiAccounting\*"' not in setup_text:
        add("installer_print_source", r"setup.iss must package the verified PyInstaller dist\AlrajhiAccounting tree")
    for token in ("print_templates.py", "_template_loader.py"):
        if token not in build:
            add("installer_print_source", f"build script must verify packaged printing runtime file {token}")

    return issues


def windows_packaging_gate_summary(root: Path | None = None) -> Dict[str, object]:
    rows = packaging_gate_matrix(root)
    issues = validate_windows_packaging_gate(root)
    categories: Dict[str, int] = {}
    for row in rows:
        categories[str(row["category"])] = categories.get(str(row["category"]), 0) + 1
    return {
        "phase": WINDOWS_PACKAGING_GATE_PHASE,
        "checks": len(rows),
        "categories": categories,
        "issues": sum(len(v) for v in issues.values()),
        "issue_groups": len(issues),
        "ready": not issues,
    }


__all__ = [
    "WINDOWS_PACKAGING_GATE_PHASE",
    "PackagingGateCheck",
    "packaging_gate_checks",
    "packaging_gate_matrix",
    "validate_windows_packaging_gate",
    "windows_packaging_gate_summary",
    "REQUIRED_GITIGNORE_BUILD_TRACKING",
]
