# -*- coding: utf-8 -*-
"""Phase 365 contract: LoginDialog restored to the Phase352 single-card layout.

The later split/RTL login experiments are intentionally superseded.  The login
screen should again use the stable Phase352 vertical card: centered logo/title,
connection badge, username field, password row, remember/language row, warning,
error label, login button, switch-account button and footer.  Later global brand
QSS/tokens remain available, but LoginDialog itself must not opt into the
first-run split panels that caused runtime overlap on the user's display.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from theme.brand import BRAND, get_tokens
from theme.qss import build_global_qss

ROOT = Path(__file__).resolve().parents[3]
LOGIN_PATH = "alrajhi_client/views/dialogs/login_dialog.py"
QSS_PATH = "alrajhi_client/theme/qss.py"

REQUIRED_PHASE352_LOGIN_MARKERS = (
    "Phase365: restored LoginDialog visual structure to Phase352 single-card design.",
    "from PyQt5.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QCheckBox, QComboBox, QFrame",
    "from PyQt5.QtGui import QPixmap",
    "from utils import focus_first_input",
    "from brand_assets import logo_png, APP_DISPLAY_NAME_AR, APP_DESCRIPTION_AR",
    "self.resize(int(BRAND.get('login_card_width', 520)), 640)",
    "self.setMinimumSize(430, 540)",
    "self.main_frame.setObjectName('loginCard')",
    "layout = QVBoxLayout(self.content_widget)",
    "layout.setSpacing(14)",
    "layout.setContentsMargins(34, 24, 34, 30)",
    "logo.setObjectName('brandMark')",
    "self.app_title_label.setObjectName(\"heroTitle\")",
    "self.subtitle_label.setObjectName('muted')",
    "pwd_layout = QHBoxLayout()",
    "pwd_layout.addWidget(self.password_edit)",
    "pwd_layout.addWidget(self.show_pwd_btn)",
    "layout.addLayout(pwd_layout)",
    "options_layout = QHBoxLayout()",
    "layout.addLayout(options_layout)",
    "self.login_btn.setObjectName(\"primary\")",
    "self.switch_btn = DesignSystem.secondary_button(translate('switch_account'))",
)

FORBIDDEN_LATER_LOGIN_MARKERS = (
    "from ui.first_run_branding import",
    "brand_side_panel(",
    "first_run_form_panel(",
    "root_layout = QHBoxLayout(self.content_widget)",
    "self.brand_panel =",
    "self.form_panel =",
    "loginLayout', 'rtl_organized_split'",
    "loginDensity', 'expanded_vertical'",
    "loginOverlapPolicy', 'sectioned_no_overlap'",
    "loginSpacingPolicy', 'password_row_reserved_gap'",
    "loginCredentialsPanel",
    "loginOptionsPanel",
    "loginPasswordRow",
    "loginPasswordSafeSpacer",
    "_apply_directional_layout",
    "_field_label(",
)

REQUIRED_QSS_MARKERS = (
    "QFrame#loginCard",
    "QLabel#brandMark",
    "QLabel#heroTitle",
    "QPushButton#primary",
)


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def login_phase352_restore_active(root: Path | None = None) -> bool:
    login = _read(LOGIN_PATH, root)
    return (
        "Phase365: restored LoginDialog visual structure to Phase352 single-card design." in login
        or "Phase367: restored LoginDialog visual structure to the pre-Phase350 original baseline." in login
    )


def login_phase352_restore_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
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
    qss_source = _read(QSS_PATH, base)
    rows: List[Dict[str, object]] = []

    if "Phase367: restored LoginDialog visual structure to the pre-Phase350 original baseline." in login:
        return [{
            "key": "phase367_superseded_by_pre350_restore",
            "category": "superseded_login_layout",
            "description": "Phase365 Phase352 login contract is intentionally superseded by Phase367 pre-Phase350 restore",
            "status": "pass",
            "detail": "LoginDialog restored to original pre-Phase350 visual structure",
            "phase": 367,
        }]

    rows.append({
        "key": "brand_phase",
        "category": "tokens",
        "description": "Brand system remains active after restoring LoginDialog to Phase352 layout",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= 365 else "fail",
        "detail": BRAND.get("brand_phase"),
        "phase": 365,
    })

    for marker in REQUIRED_PHASE352_LOGIN_MARKERS:
        rows.append({
            "key": f"login_{marker[:48]}",
            "category": "login_source",
            "description": f"LoginDialog contains restored Phase352 marker: {marker}",
            "status": "pass" if marker in login else "fail",
            "detail": marker,
            "phase": 365,
        })

    for marker in FORBIDDEN_LATER_LOGIN_MARKERS:
        rows.append({
            "key": f"forbid_{marker[:48]}",
            "category": "superseded_layout",
            "description": f"LoginDialog no longer opts into superseded split/RTL overlap layout: {marker}",
            "status": "pass" if marker not in login else "fail",
            "detail": marker,
            "phase": 365,
        })

    order_tokens = [
        "layout.addWidget(self.username_combo)",
        "layout.addLayout(pwd_layout)",
        "layout.addLayout(options_layout)",
        "layout.addWidget(self.admin_warning)",
        "layout.addWidget(self.error_label)",
        "layout.addWidget(self.login_btn)",
        "layout.addWidget(self.switch_btn)",
    ]
    positions = [login.find(token) for token in order_tokens]
    rows.append({
        "key": "single_card_vertical_order",
        "category": "layout_order",
        "description": "Single-card vertical order places password before options and actions",
        "status": "pass" if all(pos >= 0 for pos in positions) and positions == sorted(positions) else "fail",
        "detail": positions,
        "phase": 365,
    })

    for marker in REQUIRED_QSS_MARKERS:
        rows.append({
            "key": f"qss_{marker[:48]}",
            "category": "qss_source",
            "description": f"Global QSS still contains Phase352 login selector: {marker}",
            "status": "pass" if marker in qss_source else "fail",
            "detail": marker,
            "phase": 365,
        })

    for theme in ("light", "dark"):
        try:
            qss = build_global_qss(get_tokens(theme))
            ok = all(marker in qss for marker in REQUIRED_QSS_MARKERS)
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS supports restored Phase352 LoginDialog",
                "status": "pass" if ok else "fail",
                "detail": len(qss),
                "phase": 365,
            })
        except Exception as exc:
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS is safe",
                "status": "fail",
                "detail": f"{exc.__class__.__name__}: {exc}",
                "phase": 365,
            })

    return rows


def login_phase352_restore_summary(root: Path | None = None) -> Dict[str, object]:
    rows = login_phase352_restore_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "phase": 365,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_PHASE352_LOGIN_MARKERS",
    "FORBIDDEN_LATER_LOGIN_MARKERS",
    "REQUIRED_QSS_MARKERS",
    "login_phase352_restore_active",
    "login_phase352_restore_matrix",
    "login_phase352_restore_summary",
]
