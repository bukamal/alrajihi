# -*- coding: utf-8 -*-
"""Phase 434 contract: branded pre-login startup splash.

The startup splash shown before LoginDialog must be a calm identity surface with
real boot stages, not a legacy card with a yellow header, fake tab buttons or
unexplained white bars.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from theme.brand import BRAND, get_tokens
from theme.qss import build_global_qss

ROOT = Path(__file__).resolve().parents[3]
SPLASH_PATH = "alrajhi_client/views/splash_screen.py"
BRAND_PATH = "alrajhi_client/theme/brand.py"
QSS_PATH = "alrajhi_client/theme/qss.py"

REQUIRED_SPLASH_MARKERS = (
    "Phase434: branded pre-login startup splash",
    "startupSurfacePolicy",
    "phase434_prelogin_branded",
    "legacyYellowHeader",
    "interactiveStageButtons",
    "brandedStartupCard",
    "startupIdentityPanel",
    "startupBrandMark",
    "startupHeroTitle",
    "startupHeroSubtitle",
    "startupStageDatabase",
    "startupStageLicense",
    "startupStageLogin",
    "startupStageShell",
    "startupProgressTrack",
    "startupStatusLabel",
    "startupDetailLabel",
    "def _detail_for_value",
    "سيتم فتح شاشة تسجيل الدخول",
)

FORBIDDEN_SPLASH_MARKERS = (
    "DesignSystem.card_style(accent=True)",
    "background-color: white; color: #083A63; border-radius: 12px; padding: 5px 10px",
    "QProgressBar::chunk { background-color: white; border-radius: 6px; }",
    "for text in (\"قاعدة البيانات\", \"الترخيص\", \"تسجيل الدخول\", \"الواجهة\")",
)

REQUIRED_TOKEN_KEYS = (
    "startup_splash_width",
    "startup_splash_height",
    "startup_splash_logo_px",
    "startup_splash_progress_width",
    "startup_splash_progress_height",
    "startup_splash_stage_height",
)

MINIMUM_TOKEN_VALUES = {
    "startup_splash_width": 720,
    "startup_splash_height": 420,
    "startup_splash_logo_px": 76,
    "startup_splash_progress_width": 460,
}

REQUIRED_QSS_MARKERS = (
    "Phase434: branded pre-login startup splash",
    "QFrame#brandedStartupCard[startupSurfacePolicy=\"phase434_prelogin_branded\"]",
    "QFrame#startupIdentityPanel[startupIdentityPanel=\"true\"]",
    "QLabel#startupHeroTitle",
    "QLabel[startupStageChip=\"true\"]",
    "QLabel[startupStageChip=\"true\"][state=\"active\"]",
    "QProgressBar#startupProgressTrack",
    "QLabel#startupStatusLabel",
    "QLabel#startupDetailLabel",
)


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def branded_prelogin_startup_splash_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    splash = _read(SPLASH_PATH, base)
    brand = _read(BRAND_PATH, base)
    qss_source = _read(QSS_PATH, base)
    rows: List[Dict[str, object]] = []

    rows.append({
        "key": "brand_phase_434",
        "category": "tokens",
        "description": "BRAND phase records branded pre-login splash stabilization",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= 434 else "fail",
        "detail": BRAND.get("brand_phase"),
    })

    for marker in REQUIRED_SPLASH_MARKERS:
        rows.append({
            "key": f"splash_required_{marker[:40]}",
            "category": "splash_source",
            "description": f"Startup splash contains Phase434 marker: {marker}",
            "status": "pass" if marker in splash else "fail",
            "detail": marker,
        })

    for marker in FORBIDDEN_SPLASH_MARKERS:
        rows.append({
            "key": f"splash_forbidden_{marker[:40]}",
            "category": "legacy_splash_removed",
            "description": f"Legacy splash marker is absent: {marker}",
            "status": "pass" if marker not in splash else "fail",
            "detail": marker,
        })

    for key in REQUIRED_TOKEN_KEYS:
        rows.append({
            "key": f"token_{key}",
            "category": "tokens",
            "description": f"BRAND defines Phase434 token {key}",
            "status": "pass" if key in BRAND and key in brand else "fail",
            "detail": {"key": key, "value": BRAND.get(key)},
        })

    for key, minimum in MINIMUM_TOKEN_VALUES.items():
        rows.append({
            "key": f"token_min_{key}",
            "category": "token_values",
            "description": f"{key} is large enough for a horizontal branded splash",
            "status": "pass" if int(BRAND.get(key, 0)) >= minimum else "fail",
            "detail": {"actual": BRAND.get(key), "minimum": minimum},
        })

    for marker in REQUIRED_QSS_MARKERS:
        rows.append({
            "key": f"qss_{marker[:40]}",
            "category": "qss_source",
            "description": f"QSS contains branded splash marker: {marker}",
            "status": "pass" if marker in qss_source else "fail",
            "detail": marker,
        })

    for theme in ("light", "dark"):
        try:
            qss = build_global_qss(get_tokens(theme))
            ok = all(marker in qss for marker in ("Phase434", "brandedStartupCard", "startupProgressTrack"))
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS contains Phase434 splash rules",
                "status": "pass" if ok else "fail",
                "detail": len(qss),
            })
        except Exception as exc:
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS is safe",
                "status": "fail",
                "detail": f"{exc.__class__.__name__}: {exc}",
            })

    return rows


def branded_prelogin_startup_splash_summary(root: Path | None = None) -> Dict[str, object]:
    rows = branded_prelogin_startup_splash_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        category = str(row.get("category", "unknown"))
        categories[category] = categories.get(category, 0) + 1
    return {
        "phase": 434,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_SPLASH_MARKERS",
    "FORBIDDEN_SPLASH_MARKERS",
    "REQUIRED_TOKEN_KEYS",
    "REQUIRED_QSS_MARKERS",
    "MINIMUM_TOKEN_VALUES",
    "branded_prelogin_startup_splash_matrix",
    "branded_prelogin_startup_splash_summary",
]
