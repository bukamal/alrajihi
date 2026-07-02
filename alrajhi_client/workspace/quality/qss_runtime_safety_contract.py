# -*- coding: utf-8 -*-
"""Phase 357 guard contract: QSS runtime f-string safety.

The application applies the global QSS during ThemeManager.init_app().  A
single unescaped CSS brace inside build_global_qss() can pass compileall but
raise NameError/ValueError when the theme is applied.  This contract executes
QSS generation for both palettes and records the branded blocks that must keep
literal CSS braces escaped in the Python f-string source.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from theme.brand import BRAND, get_tokens
from theme.qss import build_global_qss

ROOT = Path(__file__).resolve().parents[3]
QSS_PATH = "alrajhi_client/theme/qss.py"

REQUIRED_QSS_RUNTIME_MARKERS = (
    "QTabWidget#TabbedWorkspace::pane {",
    "QFrame#UnifiedActionBar {",
    "QDialog[brandDialog=\"true\"], QMessageBox[brandDialog=\"true\"] {",
    "QFrame#ToastNotification[toastType=\"success\"] {",
    "QWidget[visualWorkspaceType=\"document\"], QWidget[visualWorkspaceType=\"operational\"]",
)

REQUIRED_ESCAPED_SOURCE_MARKERS = (
    "QTabWidget#TabbedWorkspace::pane {{",
    "QTabWidget#TabbedWorkspace QTabBar::tab:selected {{",
    "QPushButton#MainNavButton:hover {{",
    "QFrame#UnifiedActionBar {{",
    "QFrame#UnifiedActionBar QToolButton[shellChromeRole=\"primary\"] {{",
    "QDialog[brandDialog=\"true\"], QMessageBox[brandDialog=\"true\"] {{",
)


def _source(root: Path | None = None) -> str:
    return ((root or ROOT) / QSS_PATH).read_text(encoding="utf-8")


def _generate(theme: str) -> tuple[bool, str, str]:
    try:
        qss = build_global_qss(get_tokens(theme))
        return True, qss, ""
    except Exception as exc:  # pragma: no cover - failure path is guard output
        return False, "", f"{exc.__class__.__name__}: {exc}"


def qss_runtime_safety_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    rows: List[Dict[str, object]] = []
    source = _source(base)

    rows.append({
        "key": "brand_phase",
        "category": "tokens",
        "description": "BRAND phase includes QSS runtime f-string hotfix",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= 357 else "fail",
        "detail": BRAND.get("brand_phase"),
    })

    for theme in ("light", "dark"):
        ok, qss, detail = _generate(theme)
        rows.append({
            "key": f"generate_{theme}",
            "category": "runtime",
            "description": f"build_global_qss executes for {theme} theme without f-string NameError",
            "status": "pass" if ok and len(qss) > 1000 else "fail",
            "detail": detail or len(qss),
        })
        if ok:
            for marker in REQUIRED_QSS_RUNTIME_MARKERS:
                rows.append({
                    "key": f"{theme}_marker_{marker[:38]}",
                    "category": "qss_output",
                    "description": f"Generated {theme} QSS contains {marker}",
                    "status": "pass" if marker in qss else "fail",
                    "detail": marker,
                })

    for marker in REQUIRED_ESCAPED_SOURCE_MARKERS:
        rows.append({
            "key": f"escaped_source_{marker[:42]}",
            "category": "source",
            "description": f"QSS f-string source keeps literal CSS brace escaped for {marker}",
            "status": "pass" if marker in source else "fail",
            "detail": marker,
        })

    return rows


def qss_runtime_safety_summary(root: Path | None = None) -> Dict[str, object]:
    rows = qss_runtime_safety_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "phase": 357,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_QSS_RUNTIME_MARKERS",
    "REQUIRED_ESCAPED_SOURCE_MARKERS",
    "qss_runtime_safety_matrix",
    "qss_runtime_safety_summary",
]
