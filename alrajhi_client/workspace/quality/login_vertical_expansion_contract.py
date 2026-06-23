# -*- coding: utf-8 -*-
"""Phase 361 contract: vertically expanded RTL login layout.

The login screen keeps the Phase355 split identity and Phase360 RTL organization,
but increases the dialog envelope, form height, section spacing, field heights and
action button heights so Arabic labels/options do not appear compressed.
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

REQUIRED_LOGIN_VERTICAL_MARKERS = (
    "Phase361: expanded vertical login layout",
    "loginDensity', 'expanded_vertical'",
    "login_rtl_expanded_width",
    "login_rtl_expanded_height",
    "login_rtl_min_height",
    "login_form_expanded_min_height",
    "login_credentials_min_height",
    "login_options_min_height",
    "login_field_height",
    "login_action_button_height",
    "login_secondary_button_height",
    "self.credentials_panel.setMinimumHeight",
    "self.options_panel.setMinimumHeight",
    "self.username_combo.setMinimumHeight",
    "self.password_edit.setMinimumHeight",
    "self.login_btn.setMinimumHeight",
    "self.switch_btn.setMinimumHeight",
)

REQUIRED_QSS_VERTICAL_MARKERS = (
    'loginDensity="expanded_vertical"',
    "QFrame#loginCard[loginDensity=\"expanded_vertical\"] QFrame#firstRunFormPanel",
    "QFrame#loginCard[loginDensity=\"expanded_vertical\"] QFrame#loginCredentialsPanel",
    "QFrame#loginCard[loginDensity=\"expanded_vertical\"] QFrame#loginOptionsPanel",
    "QFrame#loginCard[loginDensity=\"expanded_vertical\"] QComboBox#loginUsernameCombo",
    "QFrame#loginCard[loginDensity=\"expanded_vertical\"] QPushButton#firstRunPrimary",
)

REQUIRED_BRAND_VERTICAL_KEYS = (
    "login_rtl_expanded_width",
    "login_rtl_expanded_height",
    "login_rtl_min_height",
    "login_form_expanded_min_height",
    "login_credentials_min_height",
    "login_options_min_height",
    "login_field_height",
    "login_action_button_height",
    "login_secondary_button_height",
)

MINIMUM_NUMERIC_VALUES = {
    "brand_phase": 361,
    "login_rtl_expanded_height": 740,
    "login_rtl_min_height": 700,
    "login_form_expanded_min_height": 650,
    "login_credentials_min_height": 180,
    "login_options_min_height": 92,
    "login_field_height": 46,
    "login_action_button_height": 50,
    "login_secondary_button_height": 46,
}


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def login_vertical_expansion_matrix(root: Path | None = None) -> List[Dict[str, object]]:
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
            "description": "Phase 361 login-specific layout contract is intentionally superseded by Phase365 Phase352 restore",
            "status": "pass",
            "detail": "LoginDialog restored to Phase352 single-card visual structure",
            "phase": 361,
        }]
    brand_source = _read(BRAND_PATH, base)
    qss_source = _read(QSS_PATH, base)
    rows: List[Dict[str, object]] = []

    for key, minimum in MINIMUM_NUMERIC_VALUES.items():
        value = BRAND.get(key, 0)
        rows.append({
            "key": f"metric_{key}",
            "category": "brand_metrics",
            "description": f"{key} is expanded enough for the RTL login layout",
            "status": "pass" if int(value) >= int(minimum) else "fail",
            "detail": f"{value} >= {minimum}",
            "phase": 361,
        })

    for marker in REQUIRED_BRAND_VERTICAL_KEYS:
        rows.append({
            "key": f"brand_source_{marker}",
            "category": "brand_source",
            "description": f"Brand tokens include login expansion key: {marker}",
            "status": "pass" if marker in brand_source else "fail",
            "detail": marker,
            "phase": 361,
        })

    for marker in REQUIRED_LOGIN_VERTICAL_MARKERS:
        rows.append({
            "key": f"login_{marker[:44]}",
            "category": "login_source",
            "description": f"LoginDialog uses expanded vertical marker: {marker}",
            "status": "pass" if marker in login else "fail",
            "detail": marker,
            "phase": 361,
        })

    for marker in REQUIRED_QSS_VERTICAL_MARKERS:
        rows.append({
            "key": f"qss_{marker[:44]}",
            "category": "qss_source",
            "description": f"QSS contains expanded login selector: {marker}",
            "status": "pass" if marker in qss_source else "fail",
            "detail": marker,
            "phase": 361,
        })

    for theme in ("light", "dark"):
        try:
            qss = build_global_qss(get_tokens(theme))
            ok = all(marker in qss for marker in ('loginDensity="expanded_vertical"', 'min-height: 48px', 'QFrame#loginCredentialsPanel'))
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS includes expanded login selectors and field height",
                "status": "pass" if ok else "fail",
                "detail": len(qss),
                "phase": 361,
            })
        except Exception as exc:
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS is safe",
                "status": "fail",
                "detail": f"{exc.__class__.__name__}: {exc}",
                "phase": 361,
            })

    return rows


def login_vertical_expansion_summary(root: Path | None = None) -> Dict[str, object]:
    rows = login_vertical_expansion_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "phase": 361,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_LOGIN_VERTICAL_MARKERS",
    "REQUIRED_QSS_VERTICAL_MARKERS",
    "REQUIRED_BRAND_VERTICAL_KEYS",
    "MINIMUM_NUMERIC_VALUES",
    "login_vertical_expansion_matrix",
    "login_vertical_expansion_summary",
]
