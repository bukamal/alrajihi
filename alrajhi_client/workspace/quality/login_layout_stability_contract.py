# -*- coding: utf-8 -*-
"""Phase 358 contract: stable centered login layout.

This PyQt-free contract prevents the branded login screen from returning to the
wide split layout that caused overlapping controls on smaller screens and in
long translations.  The login surface must remain centered, bounded, and use
short button labels with full tooltips.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from theme.brand import BRAND, get_tokens
from theme.qss import build_global_qss

ROOT = Path(__file__).resolve().parents[3]
LOGIN_PATH = "alrajhi_client/views/dialogs/login_dialog.py"
BRANDING_PATH = "alrajhi_client/ui/first_run_branding.py"
QSS_PATH = "alrajhi_client/theme/qss.py"

REQUIRED_LOGIN_MARKERS = (
    "loginLayout', 'stable_centered'",
    "login_brand_header(",
    "first_run_form_panel()",
    "setMaximumWidth(int(BRAND.get('login_form_max_width'",
    "QVBoxLayout(self.content_widget)",
    "QGridLayout(options_panel)",
    "loginPasswordToggle",
    "_switch_account_label",
    "self.switch_btn.setToolTip(translate('switch_account'))",
    "brand_side_panel(",
)

FORBIDDEN_LOGIN_MARKERS = (
    "root_layout = QHBoxLayout(self.content_widget)",
    "root_layout.addWidget(self.brand_panel, 0)",
    "QPushButton(translate('switch_account'))",
)

REQUIRED_HELPER_MARKERS = (
    "FIRST_RUN_RUNTIME_PHASE = 358",
    "login_brand_header",
    "firstRunLoginHeader",
    "firstRunLoginLogo",
    "firstRunLoginTitle",
    "firstRunLoginSubtitle",
    "firstRunLoginModeChip",
)

REQUIRED_QSS_MARKERS = (
    "Phase358: stable centered login layout",
    "QFrame#firstRunLoginHeader",
    "QLabel#firstRunLoginLogo",
    "QLabel#firstRunLoginTitle",
    "QLabel#firstRunLoginSubtitle",
    "QLabel#firstRunLoginModeChip",
    "QFrame#loginOptionsPanel",
    "QPushButton#loginPasswordToggle",
)

REQUIRED_TOKEN_KEYS = (
    "first_run_login_header_bg",
    "login_stable_width",
    "login_stable_height",
    "login_form_max_width",
    "brand_logo_login_header_px",
)


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def login_layout_stability_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    rows: List[Dict[str, object]] = []
    login = _read(LOGIN_PATH, base)
    helper = _read(BRANDING_PATH, base)
    qss_source = _read(QSS_PATH, base)

    rows.append({
        "key": "brand_phase",
        "category": "tokens",
        "description": "BRAND phase advanced to login layout stability hotfix",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= 358 else "fail",
        "detail": BRAND.get("brand_phase"),
    })

    for key in REQUIRED_TOKEN_KEYS:
        rows.append({
            "key": f"token_{key}",
            "category": "tokens",
            "description": f"BRAND includes {key}",
            "status": "pass" if key in BRAND or all(key in get_tokens(theme) for theme in ("light", "dark")) else "fail",
            "detail": key,
        })

    for marker in REQUIRED_LOGIN_MARKERS:
        rows.append({
            "key": f"login_{marker[:36]}",
            "category": "login_source",
            "description": f"Login dialog uses stable layout marker {marker}",
            "status": "pass" if marker in login else "fail",
            "detail": marker,
        })

    for marker in FORBIDDEN_LOGIN_MARKERS:
        rows.append({
            "key": f"forbid_{marker[:36]}",
            "category": "login_source",
            "description": f"Login dialog no longer uses overlapping layout marker {marker}",
            "status": "pass" if marker not in login else "fail",
            "detail": marker,
        })

    for marker in REQUIRED_HELPER_MARKERS:
        rows.append({
            "key": f"helper_{marker[:36]}",
            "category": "helper",
            "description": f"First-run helper exposes stable login marker {marker}",
            "status": "pass" if marker in helper else "fail",
            "detail": marker,
        })

    for marker in REQUIRED_QSS_MARKERS:
        rows.append({
            "key": f"qss_{marker[:36]}",
            "category": "qss_source",
            "description": f"QSS source contains {marker}",
            "status": "pass" if marker in qss_source else "fail",
            "detail": marker,
        })

    for theme in ("light", "dark"):
        try:
            qss = build_global_qss(get_tokens(theme))
            rows.append({
                "key": f"generate_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS includes stable login header selector",
                "status": "pass" if "QFrame#firstRunLoginHeader" in qss else "fail",
                "detail": len(qss),
            })
        except Exception as exc:  # pragma: no cover - guard output path
            rows.append({
                "key": f"generate_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS executes without f-string failure",
                "status": "fail",
                "detail": f"{exc.__class__.__name__}: {exc}",
            })

    return rows


def login_layout_stability_summary(root: Path | None = None) -> Dict[str, object]:
    rows = login_layout_stability_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "phase": 358,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_LOGIN_MARKERS",
    "FORBIDDEN_LOGIN_MARKERS",
    "REQUIRED_HELPER_MARKERS",
    "REQUIRED_QSS_MARKERS",
    "login_layout_stability_matrix",
    "login_layout_stability_summary",
]
