# -*- coding: utf-8 -*-
"""Phase 443 lazy page factory import path contract.

Phase 436 moved non-dashboard workspaces behind lazy factories to reduce the
login-to-main-window delay.  Windows runtime testing then exposed a packaging
regression: lazy factories used short module paths such as
``views.widgets.pos_widget``.  In packaged sessions those may not resolve,
leaving POS/restaurant pages as error pages.

This contract keeps lazy factory paths fully-qualified while preserving a
source-tree fallback inside the loader.  It is static and Qt-free so it can run
in CI without PyQt.
"""
from __future__ import annotations

from pathlib import Path
import ast
import json

REQUIRED_FACTORY_PATHS = {
    "dashboard": "alrajhi_client.views.widgets.dashboard_widget",
    "pos": "alrajhi_client.views.widgets.pos_widget",
    "restaurant": "alrajhi_client.views.restaurant.restaurant_simple_pos_widget",
    "cafe": "alrajhi_client.views.cafe",
    "apparel": "alrajhi_client.views.apparel",
    "reports": "alrajhi_client.views.widgets.reports_widget",
    "settings": "alrajhi_client.views.widgets.settings_widget",
    "manufacturing": "alrajhi_client.views.widgets.manufacturing_widget",
}

LEGACY_PREFIXES = ("views.", "features.", "ui.", "workspace.", "shell.")
REQUIRED_LOADER_MARKERS = [
    "normalize_page_factory_module_name",
    "page_factory_import_candidates",
    "_is_missing_candidate_module",
    "_LAZY_FACTORY_PACKAGE_PREFIX = 'alrajhi_client.'",
    "_LEGACY_FACTORY_MODULE_PREFIXES",
    "ليس خطأ REST/API",
]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def _extract_page_factory_specs(source: str) -> dict[str, tuple[str, str]]:
    tree = ast.parse(source)
    specs: dict[str, tuple[str, str]] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PAGE_FACTORY_SPECS":
                    if not isinstance(node.value, ast.Dict):
                        raise ValueError("PAGE_FACTORY_SPECS is not a dict literal")
                    for key_node, value_node in zip(node.value.keys, node.value.values):
                        if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
                            continue
                        if not isinstance(value_node, ast.Tuple) or len(value_node.elts) != 2:
                            continue
                        a, b = value_node.elts
                        if isinstance(a, ast.Constant) and isinstance(b, ast.Constant):
                            specs[key_node.value] = (str(a.value), str(b.value))
    return specs


def _module_to_rel_candidates(module_name: str) -> list[Path]:
    parts = module_name.split(".")
    return [Path(*parts).with_suffix(".py"), Path(*parts) / "__init__.py"]


def phase443_lazy_page_factory_import_path_summary(root: Path) -> dict:
    main_rel = "alrajhi_client/views/main_window.py"
    main = _read(root, main_rel)
    details: list[str] = []

    for marker in REQUIRED_LOADER_MARKERS:
        if marker not in main:
            details.append(f"main_window.py missing lazy loader marker: {marker}")

    specs = _extract_page_factory_specs(main)
    if not specs:
        details.append("PAGE_FACTORY_SPECS could not be extracted")

    for key, expected_module in REQUIRED_FACTORY_PATHS.items():
        actual = specs.get(key, (None, None))[0]
        if actual != expected_module:
            details.append(f"PAGE_FACTORY_SPECS[{key!r}] expected {expected_module!r}, found {actual!r}")

    legacy_specs = {
        key: module
        for key, (module, _class_name) in specs.items()
        if module.startswith(LEGACY_PREFIXES)
    }
    if legacy_specs:
        details.append(f"lazy factory specs still contain short module paths: {legacy_specs}")

    missing_files: dict[str, str] = {}
    for key, (module, class_name) in specs.items():
        candidates = _module_to_rel_candidates(module)
        existing = [rel for rel in candidates if (root / rel).exists()]
        if not existing:
            missing_files[key] = module
            continue
        if class_name:
            text = (root / existing[0]).read_text(encoding="utf-8", errors="ignore")
            if class_name not in text:
                details.append(f"{key}: class/export marker {class_name!r} not found in {existing[0]}")
    if missing_files:
        details.append(f"lazy factory modules without source file/package: {missing_files}")

    forbidden_substrings = [
        "('views.widgets.pos_widget'",
        "('views.restaurant.restaurant_simple_pos_widget'",
        "import_module(module_name)",
        "تحقق من اتصال الخادم أو REST",
    ]
    for token in forbidden_substrings:
        if token in main:
            details.append(f"main_window.py still contains forbidden Phase443 token: {token}")

    out_dir = root / "tools" / "audit_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "ready": not details,
        "checks": len(REQUIRED_LOADER_MARKERS) + len(specs) + len(REQUIRED_FACTORY_PATHS),
        "issues": len(details),
        "details": details,
        "spec_count": len(specs),
        "factory_specs": {key: {"module": module, "class": cls} for key, (module, cls) in specs.items()},
        "legacy_short_specs": legacy_specs,
    }
    (out_dir / "lazy_page_factory_import_path_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


__all__ = ["phase443_lazy_page_factory_import_path_summary"]
