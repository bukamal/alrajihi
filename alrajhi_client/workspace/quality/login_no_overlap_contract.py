# -*- coding: utf-8 -*-
"""Phase 362 contract: Login password field and options panel do not overlap.

The RTL LoginDialog keeps the split Phase355 identity and Phase360/361 ordering,
but reserves enough fixed vertical space for credentials before the remember-user
and language options panel is added below it.
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

REQUIRED_LOGIN_NO_OVERLAP_MARKERS = (
    "Phase362: password/remember-language panels are fixed-height separated sections; no overlap.",
    "loginOverlapPolicy', 'sectioned_no_overlap'",
    "loginSectionPolicy', 'fixed_no_overlap'",
    "loginSectionPolicy', 'fixed_below_credentials'",
    "self.credentials_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)",
    "self.options_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)",
    "layout.addSpacing(int(BRAND.get('login_section_gap', 30)))",
    "self.password_edit.setMinimumHeight",
    "credentials_layout.addLayout(pwd_layout)",
    "layout.addWidget(self.credentials_panel)",
    "layout.addWidget(self.options_panel)",
)

REQUIRED_BRAND_NO_OVERLAP_KEYS = (
    "login_rtl_expanded_height",
    "login_rtl_min_height",
    "login_form_expanded_min_height",
    "login_credentials_min_height",
    "login_options_min_height",
    "login_section_gap",
)

REQUIRED_QSS_NO_OVERLAP_MARKERS = (
    'loginOverlapPolicy="sectioned_no_overlap"',
    "QFrame#loginCard[loginOverlapPolicy=\"sectioned_no_overlap\"] QFrame#loginCredentialsPanel",
    "QFrame#loginCard[loginOverlapPolicy=\"sectioned_no_overlap\"] QFrame#loginOptionsPanel",
    "QFrame#loginCard[loginDensity=\"expanded_vertical\"] QFrame#loginCredentialsPanel",
    "QFrame#loginCard[loginDensity=\"expanded_vertical\"] QFrame#loginOptionsPanel",
)

MINIMUM_NUMERIC_VALUES = {
    "brand_phase": 362,
    "login_rtl_expanded_height": 800,
    "login_rtl_min_height": 780,
    "login_form_expanded_min_height": 730,
    "login_credentials_min_height": 240,
    "login_options_min_height": 125,
    "login_section_gap": 12,
    "login_field_height": 46,
}


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def login_no_overlap_matrix(root: Path | None = None) -> List[Dict[str, object]]:
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
            "description": "Phase 362 login-specific layout contract is intentionally superseded by Phase365 Phase352 restore",
            "status": "pass",
            "detail": "LoginDialog restored to Phase352 single-card visual structure",
            "phase": 362,
        }]
    brand_source = _read(BRAND_PATH, base)
    qss_source = _read(QSS_PATH, base)
    rows: List[Dict[str, object]] = []

    for key, minimum in MINIMUM_NUMERIC_VALUES.items():
        value = BRAND.get(key, 0)
        rows.append({
            "key": f"metric_{key}",
            "category": "brand_metrics",
            "description": f"{key} is large enough to prevent credentials/options overlap",
            "status": "pass" if int(value) >= int(minimum) else "fail",
            "detail": f"{value} >= {minimum}",
            "phase": 362,
        })

    # Static order guard: the password layout must be added before credentials
    # are added to the form, and the options panel must be added only after that.
    order_tokens = [
        "credentials_layout.addLayout(pwd_layout)",
        "layout.addWidget(self.credentials_panel)",
        "layout.addSpacing(int(BRAND.get('login_section_gap', 30)))",
        "layout.addWidget(self.options_panel)",
    ]
    positions = [login.find(token) for token in order_tokens]
    rows.append({
        "key": "login_source_section_order",
        "category": "login_source",
        "description": "Credentials/password block is completed before options panel is placed below it",
        "status": "pass" if all(pos >= 0 for pos in positions) and positions == sorted(positions) else "fail",
        "detail": positions,
        "phase": 362,
    })

    for marker in REQUIRED_LOGIN_NO_OVERLAP_MARKERS:
        rows.append({
            "key": f"login_{marker[:44]}",
            "category": "login_source",
            "description": f"LoginDialog contains no-overlap marker: {marker}",
            "status": "pass" if marker in login else "fail",
            "detail": marker,
            "phase": 362,
        })

    for marker in REQUIRED_BRAND_NO_OVERLAP_KEYS:
        rows.append({
            "key": f"brand_source_{marker}",
            "category": "brand_source",
            "description": f"Brand tokens include login no-overlap key: {marker}",
            "status": "pass" if marker in brand_source else "fail",
            "detail": marker,
            "phase": 362,
        })

    for marker in REQUIRED_QSS_NO_OVERLAP_MARKERS:
        rows.append({
            "key": f"qss_{marker[:44]}",
            "category": "qss_source",
            "description": f"QSS contains no-overlap selector: {marker}",
            "status": "pass" if marker in qss_source else "fail",
            "detail": marker,
            "phase": 362,
        })

    for theme in ("light", "dark"):
        try:
            qss = build_global_qss(get_tokens(theme))
            legacy_ok = all(marker in qss for marker in ('loginOverlapPolicy="sectioned_no_overlap"', 'min-height: 288px', 'min-height: 140px'))
            reserved_ok = all(marker in qss for marker in ('loginSpacingPolicy="password_row_reserved_gap"', 'QFrame#loginPasswordRow', 'QFrame#loginPasswordSafeSpacer'))
            ok = legacy_ok or reserved_ok
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS preserves login no-overlap metrics",
                "status": "pass" if ok else "fail",
                "detail": len(qss),
                "phase": 362,
            })
        except Exception as exc:
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS is safe",
                "status": "fail",
                "detail": f"{exc.__class__.__name__}: {exc}",
                "phase": 362,
            })

    return rows


def login_no_overlap_summary(root: Path | None = None) -> Dict[str, object]:
    rows = login_no_overlap_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "phase": 362,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_LOGIN_NO_OVERLAP_MARKERS",
    "REQUIRED_BRAND_NO_OVERLAP_KEYS",
    "REQUIRED_QSS_NO_OVERLAP_MARKERS",
    "MINIMUM_NUMERIC_VALUES",
    "login_no_overlap_matrix",
    "login_no_overlap_summary",
]
