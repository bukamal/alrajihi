# -*- coding: utf-8 -*-
"""Phase 358/359 login layout contract.

Phase 358 introduced a compact centered login layout.  The user later asked to
restore the login *design only* to the Phase 355 branded split layout while
keeping all later shell, QSS safety, dialog, table and lifecycle fixes.  This
contract therefore accepts the explicit Phase 359 rollback marker and validates
that the active LoginDialog uses the Phase 355 split surface safely.
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

PHASE359_RESTORE_MARKER = "Phase359: restored Phase355 split login design only"

REQUIRED_PHASE355_LOGIN_MARKERS = (
    PHASE359_RESTORE_MARKER,
    "Phase353: branded split login surface",
    "root_layout = QHBoxLayout(self.content_widget)",
    "brand_side_panel(",
    "root_layout.addWidget(self.brand_panel, 0)",
    "self.form_panel = first_run_form_panel()",
    "first_run_panel_width",
    "first_run_form_width",
    "brand_logo_login_px",
    "QPushButton(translate('switch_account'))",
)

FORBIDDEN_RESTORED_LOGIN_MARKERS = (
    "loginLayout', 'stable_centered'",
    "login_brand_header(",
    "setMaximumWidth(int(BRAND.get('login_form_max_width'",
    "QGridLayout(options_panel)",
    "loginPasswordToggle",
)

REQUIRED_HELPER_MARKERS = (
    "brand_side_panel",
    "firstRunBrandPanel",
    "first_run_form_panel",
    "firstRunFormPanel",
    "set_first_run_primary",
    "set_first_run_secondary",
)

REQUIRED_QSS_MARKERS = (
    "QFrame#firstRunBrandPanel",
    "QFrame#firstRunFormPanel",
    "QLabel#firstRunHeroTitle",
    "QLabel#firstRunFormTitle",
    "QPushButton#firstRunPrimary",
    "QPushButton#firstRunSecondary",
)

REQUIRED_TOKEN_KEYS = (
    "first_run_panel_width",
    "first_run_form_width",
    "brand_logo_login_px",
)


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def login_layout_stability_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    rows: List[Dict[str, object]] = []
    login = _read(LOGIN_PATH, base)
    if "Phase431: horizontal branded login layout" in login:
        return [{
            "key": "phase431_horizontal_branded_login",
            "category": "superseded_login_layout",
            "description": "Earlier login layout contract is intentionally superseded by Phase431 horizontal branded LoginDialog",
            "status": "pass",
            "detail": "LoginDialog now uses horizontal_branded_split",
            "phase": 431,
        }]
    if "Phase367: restored LoginDialog visual structure to the pre-Phase350 original baseline." in login:
        return [{
            "key": "phase367_superseded_by_pre350_restore",
            "category": "superseded_login_layout",
            "description": "Earlier experimental login layout contract is intentionally superseded by Phase367 pre-Phase350 restore",
            "status": "pass",
            "detail": "LoginDialog restored to the pre-Phase350 original visual structure",
            "phase": 367,
        }]
    if "Phase365: restored LoginDialog visual structure to Phase352 single-card design." in login:
        return [{
            "key": "phase365_superseded_by_phase352_restore",
            "category": "superseded_login_layout",
            "description": "Phase 358 login-specific layout contract is intentionally superseded by Phase365 Phase352 restore",
            "status": "pass",
            "detail": "LoginDialog restored to Phase352 single-card visual structure",
            "phase": 358,
        }]
    helper = _read(BRANDING_PATH, base)
    qss_source = _read(QSS_PATH, base)

    rows.append({
        "key": "brand_phase",
        "category": "tokens",
        "description": "BRAND phase remains at or beyond the identity-login work",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= 358 else "fail",
        "detail": BRAND.get("brand_phase"),
    })

    for key in REQUIRED_TOKEN_KEYS:
        rows.append({
            "key": f"token_{key}",
            "category": "tokens",
            "description": f"BRAND includes Phase355 login token {key}",
            "status": "pass" if key in BRAND or all(key in get_tokens(theme) for theme in ("light", "dark")) else "fail",
            "detail": key,
        })

    for marker in REQUIRED_PHASE355_LOGIN_MARKERS:
        rows.append({
            "key": f"login_{marker[:36]}",
            "category": "login_source",
            "description": f"Login dialog uses restored Phase355 marker {marker}",
            "status": "pass" if marker in login else "fail",
            "detail": marker,
        })

    for marker in FORBIDDEN_RESTORED_LOGIN_MARKERS:
        rows.append({
            "key": f"forbid_{marker[:36]}",
            "category": "login_source",
            "description": f"Login dialog no longer uses Phase358 centered-only marker {marker}",
            "status": "pass" if marker not in login else "fail",
            "detail": marker,
        })

    for marker in REQUIRED_HELPER_MARKERS:
        rows.append({
            "key": f"helper_{marker[:36]}",
            "category": "helper",
            "description": f"First-run helper exposes split login marker {marker}",
            "status": "pass" if marker in helper else "fail",
            "detail": marker,
        })

    for marker in REQUIRED_QSS_MARKERS:
        rows.append({
            "key": f"qss_{marker[:36]}",
            "category": "qss_source",
            "description": f"QSS source contains split login selector {marker}",
            "status": "pass" if marker in qss_source else "fail",
            "detail": marker,
        })

    for theme in ("light", "dark"):
        try:
            qss = build_global_qss(get_tokens(theme))
            rows.append({
                "key": f"generate_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS includes Phase355 split selectors and is f-string safe",
                "status": "pass" if "QFrame#firstRunBrandPanel" in qss and "QFrame#firstRunFormPanel" in qss else "fail",
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
        "phase": 359,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "PHASE359_RESTORE_MARKER",
    "REQUIRED_PHASE355_LOGIN_MARKERS",
    "FORBIDDEN_RESTORED_LOGIN_MARKERS",
    "REQUIRED_HELPER_MARKERS",
    "REQUIRED_QSS_MARKERS",
    "login_layout_stability_matrix",
    "login_layout_stability_summary",
]
