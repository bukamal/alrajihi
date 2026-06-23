# -*- coding: utf-8 -*-
"""Phase 363 contract: extra vertical gap below password row in LoginDialog.

Superseded by Phase364.  The guard now accepts either the original Phase363
QSS-margin policy or the stronger Phase364 reserved password-row policy.
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

REQUIRED_LOGIN_GAP_MARKERS = (
    "Phase363: explicit extra spacing below password row before remember/language panel.",
    "loginSpacingPolicy', 'password_options_gap'",
    "credentials_layout.addSpacing(int(BRAND.get('login_password_bottom_gap', 18)))",
    "layout.addSpacing(int(BRAND.get('login_section_gap', 30)))",
    "self.credentials_panel.setFixedHeight(int(BRAND.get('login_credentials_min_height', 288)))",
    "self.options_panel.setFixedHeight(int(BRAND.get('login_options_min_height', 140)))",
)

REQUIRED_QSS_GAP_MARKERS = (
    'loginSpacingPolicy="password_options_gap"',
    "QFrame#loginCard[loginSpacingPolicy=\"password_options_gap\"] QFrame#loginCredentialsPanel",
    "QFrame#loginCard[loginSpacingPolicy=\"password_options_gap\"] QLineEdit#loginPasswordEdit",
    "login_password_bottom_gap",
)

MINIMUM_NUMERIC_VALUES = {
    "brand_phase": 363,
    "login_rtl_expanded_height": 860,
    "login_rtl_min_height": 830,
    "login_form_expanded_min_height": 790,
    "login_credentials_min_height": 280,
    "login_options_min_height": 138,
    "login_section_gap": 28,
    "login_password_bottom_gap": 16,
    "login_field_height": 48,
}


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def login_password_gap_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    login = _read(LOGIN_PATH, base)
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
            "description": "Phase 363 login-specific layout contract is intentionally superseded by Phase365 Phase352 restore",
            "status": "pass",
            "detail": "LoginDialog restored to Phase352 single-card visual structure",
            "phase": 363,
        }]
    brand_source = _read(BRAND_PATH, base)
    qss_source = _read(QSS_PATH, base)
    rows: List[Dict[str, object]] = []

    for key, minimum in MINIMUM_NUMERIC_VALUES.items():
        value = BRAND.get(key, 0)
        rows.append({
            "key": f"metric_{key}",
            "category": "brand_metrics",
            "description": f"{key} reserves enough vertical space for password/options separation",
            "status": "pass" if int(value) >= int(minimum) else "fail",
            "detail": f"{value} >= {minimum}",
            "phase": 363,
        })

    order_tokens = [
        "credentials_layout.addLayout(pwd_layout)",
        "credentials_layout.addSpacing(int(BRAND.get('login_password_bottom_gap', 18)))",
        "layout.addWidget(self.credentials_panel)",
        "layout.addSpacing(int(BRAND.get('login_section_gap', 30)))",
        "layout.addWidget(self.options_panel)",
    ]
    positions = [login.find(token) for token in order_tokens]
    rows.append({
        "key": "login_source_password_gap_order",
        "category": "login_source",
        "description": "Password row receives an explicit bottom gap before the options panel",
        "status": "pass" if all(pos >= 0 for pos in positions) and positions == sorted(positions) else "fail",
        "detail": positions,
        "phase": 363,
    })

    for marker in REQUIRED_LOGIN_GAP_MARKERS:
        rows.append({
            "key": f"login_{marker[:44]}",
            "category": "login_source",
            "description": f"LoginDialog contains Phase363 gap marker: {marker}",
            "status": "pass" if marker in login else "fail",
            "detail": marker,
            "phase": 363,
        })

    for marker in ("login_password_bottom_gap", "login_section_gap", "login_credentials_min_height", "login_options_min_height"):
        rows.append({
            "key": f"brand_source_{marker}",
            "category": "brand_source",
            "description": f"Brand tokens include Phase363 spacing key: {marker}",
            "status": "pass" if marker in brand_source else "fail",
            "detail": marker,
            "phase": 363,
        })

    for marker in REQUIRED_QSS_GAP_MARKERS:
        rows.append({
            "key": f"qss_{marker[:44]}",
            "category": "qss_source",
            "description": f"QSS contains Phase363 password/options gap selector: {marker}",
            "status": "pass" if marker in qss_source else "fail",
            "detail": marker,
            "phase": 363,
        })

    for theme in ("light", "dark"):
        try:
            qss = build_global_qss(get_tokens(theme))
            legacy_ok = all(marker in qss for marker in (
                'loginSpacingPolicy="password_options_gap"',
                'margin-bottom: 18px',
            ))
            reserved_ok = all(marker in qss for marker in (
                'loginSpacingPolicy="password_row_reserved_gap"',
                'QFrame#loginPasswordRow',
                'QFrame#loginPasswordSafeSpacer',
            ))
            ok = legacy_ok or reserved_ok
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS preserves Phase363 password/options gap metrics",
                "status": "pass" if ok else "fail",
                "detail": len(qss),
                "phase": 363,
            })
        except Exception as exc:
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS is safe",
                "status": "fail",
                "detail": f"{exc.__class__.__name__}: {exc}",
                "phase": 363,
            })

    return rows


def login_password_gap_summary(root: Path | None = None) -> Dict[str, object]:
    rows = login_password_gap_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "phase": 363,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_LOGIN_GAP_MARKERS",
    "REQUIRED_QSS_GAP_MARKERS",
    "MINIMUM_NUMERIC_VALUES",
    "login_password_gap_matrix",
    "login_password_gap_summary",
]
