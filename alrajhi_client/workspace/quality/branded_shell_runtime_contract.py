# -*- coding: utf-8 -*-
"""Phase 354 branded tabs/menu/action-bar runtime contract.

This contract is PyQt-free. It verifies that the visual identity layer introduced
for the first-run screens is now applied to the daily shell chrome: workspace
tabs, main menu buttons, dropdown menus and the shared action bar.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from theme.brand import BRAND, get_tokens
from theme.shell_identity import (
    REQUIRED_SHELL_OBJECT_NAMES,
    REQUIRED_SHELL_QSS_MARKERS,
    REQUIRED_SHELL_TOKEN_KEYS,
    SHELL_IDENTITY_PHASE,
    shell_identity_matrix,
    validate_shell_identity_tokens,
)

ROOT = Path(__file__).resolve().parents[3]

REQUIRED_SHELL_FILES = (
    "alrajhi_client/theme/shell_identity.py",
    "alrajhi_client/shell/tab_label_policy.py",
    "alrajhi_client/shell/tab_workspace.py",
    "alrajhi_client/shell/unified_action_bar.py",
    "alrajhi_client/views/main_window.py",
    "alrajhi_client/theme/qss.py",
)

REQUIRED_RUNTIME_MARKERS = {
    "alrajhi_client/shell/tab_label_policy.py": (
        "BRANDED_TAB_PHASE = 354",
        "compose_tab_label",
        "label_for_kind",
        "رئيسي",
        "فرعي",
    ),
    "alrajhi_client/shell/tab_workspace.py": (
        "BRANDED_TABS_PHASE = 354",
        "compose_tab_label",
        "_apply_tab_identity",
        "setTabToolTip",
        "setTabData",
        "brandedTabs",
    ),
    "alrajhi_client/shell/unified_action_bar.py": (
        "BRANDED_ACTION_BAR_PHASE = 354",
        "shellChromeRole",
        "ActionBarButton_save",
        "ActionBarButton_print",
        "Phase354: branded icon menu and action bar runtime",
    ),
    "alrajhi_client/views/main_window.py": (
        "navigation_bar_stylesheet",
        "shellChromeRole",
        "MainNavToolButton",
        "menuLabel",
        "Phase354: branded icon menu and action bar runtime",
    ),
}


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def branded_shell_runtime_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    rows: List[Dict[str, object]] = []

    rows.append({
        "key": "brand_phase",
        "category": "tokens",
        "description": "BRAND phase advanced to branded shell runtime polish",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= SHELL_IDENTITY_PHASE else "fail",
        "detail": BRAND.get("brand_phase"),
    })

    for theme in ("light", "dark"):
        issues = validate_shell_identity_tokens(get_tokens(theme))
        rows.append({
            "key": f"{theme}_shell_tokens",
            "category": "tokens",
            "description": f"{theme} palette includes Phase {SHELL_IDENTITY_PHASE} shell tokens",
            "status": "pass" if not issues else "fail",
            "detail": "; ".join(f"{k}:{','.join(v)}" for k, v in issues.items()),
        })

    for item in shell_identity_matrix(get_tokens("light")):
        rows.append({
            "key": f"shell_{item['kind']}_{item['key']}",
            "category": str(item["kind"]),
            "description": item["description"],
            "status": "pass" if item.get("present", True) else "fail",
            "detail": item["key"],
        })

    for path in REQUIRED_SHELL_FILES:
        rows.append({
            "key": f"file_{Path(path).stem}",
            "category": "file",
            "description": "Required branded shell runtime file exists",
            "status": "pass" if (base / path).exists() else "fail",
            "detail": path,
        })

    qss = _read("alrajhi_client/theme/qss.py", base)
    for marker in REQUIRED_SHELL_QSS_MARKERS:
        rows.append({
            "key": f"qss_{marker[:36]}",
            "category": "qss",
            "description": f"QSS contains {marker}",
            "status": "pass" if marker in qss else "fail",
            "detail": marker,
        })

    searchable_paths = tuple(REQUIRED_RUNTIME_MARKERS.keys()) + ("alrajhi_client/theme/qss.py",)
    for object_name in REQUIRED_SHELL_OBJECT_NAMES:
        found = any(object_name in _read(path, base) for path in searchable_paths)
        rows.append({
            "key": f"object_{object_name}",
            "category": "object_name",
            "description": "Required shell object name/role is present in runtime code",
            "status": "pass" if found else "fail",
            "detail": object_name,
        })

    for path, markers in REQUIRED_RUNTIME_MARKERS.items():
        text = _read(path, base)
        for marker in markers:
            rows.append({
                "key": f"runtime_{Path(path).stem}_{marker[:24]}",
                "category": "runtime",
                "description": f"{path} uses {marker}",
                "status": "pass" if marker in text else "fail",
                "detail": marker,
            })

    return rows


def branded_shell_runtime_summary(root: Path | None = None) -> Dict[str, object]:
    rows = branded_shell_runtime_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "phase": SHELL_IDENTITY_PHASE,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_SHELL_FILES",
    "REQUIRED_RUNTIME_MARKERS",
    "branded_shell_runtime_matrix",
    "branded_shell_runtime_summary",
]
