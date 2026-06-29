# -*- coding: utf-8 -*-
"""Qt-free audit for Phase444 lazy page packaging safety."""
from __future__ import annotations

import ast
import csv
import json
from pathlib import Path
from typing import Any

from .lazy_page_runtime_packaging_contract import (
    PHASE,
    REQUIRED_COLLECT_SUBMODULES,
    CRITICAL_LAZY_PAGE_IDS,
)

ROOT = Path(__file__).resolve().parents[3]
MAIN_WINDOW = ROOT / "alrajhi_client" / "views" / "main_window.py"
MANIFEST = ROOT / "build" / "pyinstaller_hidden_imports.py"
BUILD_PS1 = ROOT / "build" / "build_windows.ps1"
OUT_DIR = ROOT / "tools" / "audit_outputs"
MATRIX = OUT_DIR / "lazy_page_runtime_packaging_matrix.csv"
SUMMARY = OUT_DIR / "lazy_page_runtime_packaging_summary.json"


def _literal_assignments(path: Path) -> dict[str, Any]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        result[target.id] = ast.literal_eval(node.value)
                    except Exception:
                        pass
    return result


def load_page_factory_specs() -> dict[str, tuple[str, str]]:
    data = _literal_assignments(MAIN_WINDOW)
    specs = data.get("PAGE_FACTORY_SPECS", {})
    return {str(k): (str(v[0]), str(v[1])) for k, v in specs.items() if isinstance(v, (tuple, list)) and len(v) == 2}


def load_packaging_manifest() -> tuple[set[str], set[str]]:
    data = _literal_assignments(MANIFEST)
    return set(data.get("COLLECT_SUBMODULES", [])), set(data.get("HIDDEN_IMPORTS", []))


def module_to_file_candidates(module_name: str) -> list[Path]:
    rel = Path(*module_name.split("."))
    return [ROOT / rel.with_suffix(".py"), ROOT / rel / "__init__.py"]


def module_exists(module_name: str) -> bool:
    return any(p.exists() for p in module_to_file_candidates(module_name))


def is_collected(module_name: str, collect_submodules: set[str]) -> bool:
    return any(module_name == item or module_name.startswith(f"{item}.") for item in collect_submodules)


def run_audit(write_outputs: bool = True) -> dict[str, Any]:
    specs = load_page_factory_specs()
    collect, hidden = load_packaging_manifest()
    build_text = BUILD_PS1.read_text(encoding="utf-8", errors="replace") if BUILD_PS1.exists() else ""

    rows: list[dict[str, Any]] = []
    errors: list[str] = []

    for required in sorted(REQUIRED_COLLECT_SUBMODULES):
        ok_manifest = required in collect
        ok_build = f"--collect-submodules {required}" in build_text
        rows.append({
            "kind": "collect_submodules",
            "page_id": "",
            "module": required,
            "class": "",
            "manifest": ok_manifest,
            "build_script": ok_build,
            "module_exists": module_exists(required),
            "status": "ok" if ok_manifest and ok_build and module_exists(required) else "fail",
        })
        if not (ok_manifest and ok_build and module_exists(required)):
            errors.append(f"collect-submodules not fully wired: {required}")

    for page_id, (module_name, class_name) in sorted(specs.items()):
        exists = module_exists(module_name)
        collected = is_collected(module_name, collect)
        hidden_ok = module_name in hidden or collected
        build_ok = (f"--hidden-import {module_name}" in build_text) or any(
            f"--collect-submodules {item}" in build_text and (module_name == item or module_name.startswith(f"{item}."))
            for item in collect
        )
        critical = page_id in CRITICAL_LAZY_PAGE_IDS
        status = "ok" if exists and hidden_ok and build_ok else ("fail" if critical else "warn")
        rows.append({
            "kind": "lazy_page_factory",
            "page_id": page_id,
            "module": module_name,
            "class": class_name,
            "manifest": hidden_ok,
            "build_script": build_ok,
            "module_exists": exists,
            "status": status,
        })
        if status == "fail":
            errors.append(f"critical lazy page is not packaging-safe: {page_id} -> {module_name}.{class_name}")

    summary = {
        "phase": PHASE,
        "spec_count": len(specs),
        "critical_page_count": len(CRITICAL_LAZY_PAGE_IDS),
        "rows": len(rows),
        "errors": errors,
        "ok": not errors,
        "matrix": str(MATRIX.relative_to(ROOT)),
    }

    if write_outputs:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        with MATRIX.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["kind", "page_id", "module", "class", "manifest", "build_script", "module_exists", "status"])
            writer.writeheader()
            writer.writerows(rows)
        SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    return summary


__all__ = [
    "run_audit",
    "load_page_factory_specs",
    "load_packaging_manifest",
    "module_exists",
    "is_collected",
]
