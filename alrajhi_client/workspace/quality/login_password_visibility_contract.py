# -*- coding: utf-8 -*-
"""Phase 364 contract: Login password row remains fully visible above options.

This supersedes the Phase363 stylesheet-margin approach.  The password field now
lives inside a reserved row container, followed by a real spacer widget before
remember/language options.  This makes the vertical separation part of the Qt
layout, not only painted CSS margin.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from theme.brand import BRAND, get_tokens
from theme.qss import build_global_qss

ROOT = Path(__file__).resolve().parents[3]
LOGIN_PATH = "alrajhi_client/views/dialogs/login_dialog.py"
BRAND_PATH = "alrajhi_client/theme/brand.py"
QSS_PATH = "alrajhi_client/theme/qss.py"

REQUIRED_LOGIN_MARKERS = (
    "Phase364: password field gets its own reserved row and visible spacer before options.",
    "loginSpacingPolicy', 'password_row_reserved_gap'",
    "self.password_row = QFrame()",
    "self.password_row.setObjectName('loginPasswordRow')",
    "self.password_row.setFixedHeight(int(BRAND.get('login_password_row_height', 68)))",
    "pwd_layout = QHBoxLayout(self.password_row)",
    "credentials_layout.addWidget(self.password_row)",
    "self.password_safe_spacer = QFrame()",
    "self.password_safe_spacer.setObjectName('loginPasswordSafeSpacer')",
    "self.password_safe_spacer.setFixedHeight(int(BRAND.get('login_password_options_spacer_height', 46)))",
    "credentials_layout.addWidget(self.password_safe_spacer)",
    "self.show_pwd_btn.setObjectName('loginPasswordVisibilityButton')",
)

REQUIRED_QSS_MARKERS = (
    'loginSpacingPolicy="password_row_reserved_gap"',
    'QFrame#loginPasswordRow',
    'QFrame#loginPasswordSafeSpacer',
    'login_password_row_height',
    'login_password_options_spacer_height',
)

MINIMUM_NUMERIC_VALUES = {
    "brand_phase": 364,
    "login_rtl_expanded_height": 930,
    "login_rtl_min_height": 890,
    "login_form_expanded_min_height": 850,
    "login_credentials_min_height": 340,
    "login_password_row_height": 64,
    "login_password_options_spacer_height": 40,
    "login_options_min_height": 148,
    "login_section_gap": 36,
    "login_field_height": 52,
}


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def _credentials_minimum_height() -> int:
    """Conservative layout model for the credentials panel.

    Margins: top 24 + bottom 46.
    Items: username label, username combo, password label, password row, reserved spacer.
    Spacing: four gaps in the credentials VBox.
    Labels are estimated at 22px, intentionally above the expected font height.
    """
    field = int(BRAND.get("login_field_height", 52))
    row = int(BRAND.get("login_password_row_height", 68))
    spacer = int(BRAND.get("login_password_options_spacer_height", 46))
    return 24 + 46 + 22 + field + 22 + row + spacer + (4 * 18)


def login_password_visibility_matrix(root: Path | None = None) -> List[Dict[str, object]]:
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
            "description": "Phase 364 login-specific layout contract is intentionally superseded by Phase365 Phase352 restore",
            "status": "pass",
            "detail": "LoginDialog restored to Phase352 single-card visual structure",
            "phase": 364,
        }]
    brand_source = _read(BRAND_PATH, base)
    qss_source = _read(QSS_PATH, base)
    rows: List[Dict[str, object]] = []

    for key, minimum in MINIMUM_NUMERIC_VALUES.items():
        value = BRAND.get(key, 0)
        rows.append({
            "key": f"metric_{key}",
            "category": "brand_metrics",
            "description": f"{key} reserves enough room for a visible password field",
            "status": "pass" if int(value) >= int(minimum) else "fail",
            "detail": f"{value} >= {minimum}",
            "phase": 364,
        })

    required = _credentials_minimum_height()
    actual = int(BRAND.get("login_credentials_min_height", 0))
    rows.append({
        "key": "credentials_height_model",
        "category": "layout_model",
        "description": "Credentials panel height covers labels, fields, password row and spacer",
        "status": "pass" if actual >= required else "fail",
        "detail": f"actual={actual}, required={required}",
        "phase": 364,
    })

    order_tokens = [
        "self.password_label = self._field_label(translate('password'))",
        "self.password_row = QFrame()",
        "credentials_layout.addWidget(self.password_row)",
        "self.password_safe_spacer = QFrame()",
        "credentials_layout.addWidget(self.password_safe_spacer)",
        "layout.addWidget(self.credentials_panel)",
        "layout.addSpacing(int(BRAND.get('login_section_gap', 38)))",
        "self.options_panel = QFrame()",
    ]
    positions = [login.find(token) for token in order_tokens]
    rows.append({
        "key": "password_row_before_options_order",
        "category": "login_source",
        "description": "Password row and reserved spacer appear before the options panel",
        "status": "pass" if all(pos >= 0 for pos in positions) and positions == sorted(positions) else "fail",
        "detail": positions,
        "phase": 364,
    })

    for marker in REQUIRED_LOGIN_MARKERS:
        rows.append({
            "key": f"login_{marker[:48]}",
            "category": "login_source",
            "description": f"LoginDialog contains Phase364 marker: {marker}",
            "status": "pass" if marker in login else "fail",
            "detail": marker,
            "phase": 364,
        })

    for marker in ("login_password_row_height", "login_password_options_spacer_height", "login_credentials_min_height"):
        rows.append({
            "key": f"brand_{marker}",
            "category": "brand_source",
            "description": f"Brand tokens include Phase364 spacing key: {marker}",
            "status": "pass" if marker in brand_source else "fail",
            "detail": marker,
            "phase": 364,
        })

    for marker in REQUIRED_QSS_MARKERS:
        rows.append({
            "key": f"qss_{marker[:48]}",
            "category": "qss_source",
            "description": f"QSS contains Phase364 selector/token: {marker}",
            "status": "pass" if marker in qss_source else "fail",
            "detail": marker,
            "phase": 364,
        })

    for theme in ("light", "dark"):
        try:
            qss = build_global_qss(get_tokens(theme))
            ok = all(marker in qss for marker in (
                'loginSpacingPolicy="password_row_reserved_gap"',
                'QFrame#loginPasswordRow',
                'QFrame#loginPasswordSafeSpacer',
                f"min-height: {BRAND.get('login_password_row_height', 68)}px",
                f"min-height: {BRAND.get('login_password_options_spacer_height', 46)}px",
            ))
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS preserves reserved password row and spacer",
                "status": "pass" if ok else "fail",
                "detail": len(qss),
                "phase": 364,
            })
        except Exception as exc:
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS is safe",
                "status": "fail",
                "detail": f"{exc.__class__.__name__}: {exc}",
                "phase": 364,
            })

    return rows


def login_password_visibility_summary(root: Path | None = None) -> Dict[str, object]:
    rows = login_password_visibility_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "phase": 364,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_LOGIN_MARKERS",
    "REQUIRED_QSS_MARKERS",
    "MINIMUM_NUMERIC_VALUES",
    "login_password_visibility_matrix",
    "login_password_visibility_summary",
]
