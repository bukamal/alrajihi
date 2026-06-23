# -*- coding: utf-8 -*-
"""Phase 352 brand identity visual contract.

PyQt-free contract used by guards and tests to keep visual identity tokens,
first-run screens, shell chrome and table/dialog styling unified.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from theme.brand import BRAND, get_tokens
from theme.identity import (
    IDENTITY_PHASE,
    IDENTITY_SOURCE_LOGO,
    REQUIRED_BRAND_TOKEN_KEYS,
    BRAND_SURFACES,
    brand_identity_matrix,
    validate_brand_identity_tokens,
)

ROOT = Path(__file__).resolve().parents[3]

REQUIRED_QSS_MARKERS = (
    "Phase352: branded main/sub tab labels",
    "QTabBar::tab:selected",
    "QTabBar::close-button:hover",
    "Phase352: branded menu and action chrome",
    "Phase352: first-run and licensing identity surfaces",
    "Phase352: branded dialogs and system windows",
    "QFrame#startupCard",
    "QFrame#loginCard",
    "QFrame#activationCard",
    "QLabel#brandMark",
)

REQUIRED_RUNTIME_FILES = (
    "alrajhi_client/theme/brand.py",
    "alrajhi_client/theme/identity.py",
    "alrajhi_client/theme/qss.py",
    "alrajhi_client/ui/design_system.py",
    "alrajhi_client/views/splash_screen.py",
    "alrajhi_client/views/dialogs/login_dialog.py",
    "alrajhi_client/views/dialogs/activation_dialog.py",
)

REQUIRED_SCREEN_MARKERS = {
    "alrajhi_client/views/splash_screen.py": ("brandMark", "brand_logo_large_px", "splash_width"),
    "alrajhi_client/views/dialogs/login_dialog.py": ("brandMark", "brand_logo_login_px", "login_card_width"),
    "alrajhi_client/views/dialogs/activation_dialog.py": ("brandMark", "brand_logo_login_px", "activation_card_width"),
    "alrajhi_client/ui/design_system.py": ("brand_gradient", "apply_visual_role", "BRAND_BUTTON_MIN_HEIGHT"),
}


def _read(path: str, root: Path | None = None) -> str:
    base = root or ROOT
    return (base / path).read_text(encoding="utf-8")


def brand_identity_visual_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    rows: List[Dict[str, object]] = []

    logo_path = base / IDENTITY_SOURCE_LOGO
    rows.append({
        "key": "brand_logo_asset",
        "category": "assets",
        "description": "Bundled logo asset used as visual identity source",
        "status": "pass" if logo_path.exists() else "fail",
        "detail": str(logo_path.relative_to(base)) if logo_path.exists() else "missing logo asset",
    })

    for theme in ("light", "dark"):
        issues = validate_brand_identity_tokens(get_tokens(theme))
        rows.append({
            "key": f"{theme}_brand_tokens",
            "category": "tokens",
            "description": f"{theme} palette contains all Phase {IDENTITY_PHASE} identity tokens",
            "status": "pass" if not issues else "fail",
            "detail": "; ".join(f"{k}:{','.join(v)}" for k, v in issues.items()),
        })

    for row in brand_identity_matrix(get_tokens("light")):
        rows.append({
            "key": f"identity_{row['key']}",
            "category": str(row["kind"]),
            "description": str(row["description"]),
            "status": "pass" if row.get("present", True) else "fail",
            "detail": row.get("missing", ""),
        })

    for path in REQUIRED_RUNTIME_FILES:
        rows.append({
            "key": f"file_{path}",
            "category": "file",
            "description": "Required brand runtime file exists",
            "status": "pass" if (base / path).exists() else "fail",
            "detail": path,
        })

    qss = _read("alrajhi_client/theme/qss.py", base)
    for marker in REQUIRED_QSS_MARKERS:
        rows.append({
            "key": f"qss_{marker[:32]}",
            "category": "qss",
            "description": f"QSS contains {marker}",
            "status": "pass" if marker in qss else "fail",
            "detail": marker,
        })

    for path, markers in REQUIRED_SCREEN_MARKERS.items():
        text = _read(path, base)
        for marker in markers:
            rows.append({
                "key": f"screen_{Path(path).stem}_{marker}",
                "category": "screen",
                "description": f"{path} consumes brand marker {marker}",
                "status": "pass" if marker in text else "fail",
                "detail": path,
            })

    return rows


def brand_identity_visual_summary(root: Path | None = None) -> Dict[str, object]:
    rows = brand_identity_visual_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "phase": IDENTITY_PHASE,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_BRAND_TOKEN_KEYS",
    "BRAND_SURFACES",
    "REQUIRED_QSS_MARKERS",
    "REQUIRED_RUNTIME_FILES",
    "REQUIRED_SCREEN_MARKERS",
    "brand_identity_visual_matrix",
    "brand_identity_visual_summary",
]
