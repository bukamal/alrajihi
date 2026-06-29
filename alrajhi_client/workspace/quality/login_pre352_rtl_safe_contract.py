# -*- coding: utf-8 -*-
"""Phase 366 contract: restore the pre-Phase352 login structure and apply safe RTL ordering.

Root-cause summary: the Phase360-364 login attempts introduced nested form and
options panels with fixed heights/margins.  On some DPI/font combinations Qt kept
panel geometries while QSS margins/padding changed paint bounds, so the options
panel could visually cover the password row.  The fix is to return to the
pre-Phase352 single-card QVBox/QHBox structure and apply RTL improvements only as
real layout children: explicit field labels, directional alignment, and a real
layout spacer between the password row and remember/language row.  No fixed-height
login panels or QSS-only spacing are allowed in LoginDialog.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from theme.brand import BRAND, get_tokens
from theme.qss import build_global_qss

ROOT = Path(__file__).resolve().parents[3]
LOGIN_PATH = "alrajhi_client/views/dialogs/login_dialog.py"
QSS_PATH = "alrajhi_client/theme/qss.py"

REQUIRED_MARKERS = (
    "Phase366: restored pre-Phase352 LoginDialog structure with safe RTL ordering and no overlap panels.",
    "self.resize(500, 660)",
    "self.setMinimumSize(430, 600)",
    "self.main_frame.setProperty('loginLayoutPolicy', 'pre352_rtl_ordered_no_overlay')",
    "layout = QVBoxLayout(self.content_widget)",
    "layout.setContentsMargins(34, 24, 34, 30)",
    "logo.setPixmap(QPixmap(logo_png(128)).scaled(94, 94, Qt.KeepAspectRatio, Qt.SmoothTransformation))",
    "self.username_label = self._field_label(translate('username'))",
    "self.password_label = self._field_label(translate('password'))",
    "self.username_combo.setObjectName('loginUsernameField')",
    "self.password_edit.setObjectName('loginPasswordField')",
    "self.show_pwd_btn.setObjectName('loginPasswordToggleButton')",
    "layout.addSpacing(18)",
    "options_layout = QHBoxLayout()",
    "options_layout.setObjectName('loginRememberLanguageRow')",
    "self.lang_combo.setObjectName('loginLanguageField')",
    "def _apply_directional_alignment(self):",
    "self._apply_directional_alignment()",
)

FORBIDDEN_MARKERS = (
    "from ui.first_run_branding import",
    "brand_side_panel(",
    "first_run_form_panel(",
    "root_layout = QHBoxLayout(self.content_widget)",
    "firstRunBrandPanel",
    "firstRunFormPanel",
    "loginCredentialsPanel",
    "loginOptionsPanel",
    "loginPasswordRow",
    "loginPasswordSafeSpacer",
    "setFixedHeight(int(BRAND.get('login_credentials_min_height'",
    "setFixedHeight(int(BRAND.get('login_options_min_height'",
    "loginOverlapPolicy",
    "loginSpacingPolicy",
    "loginDensity",
)

ORDER_TOKENS = (
    "self.username_label = self._field_label(translate('username'))",
    "layout.addWidget(self.username_combo)",
    "self.password_label = self._field_label(translate('password'))",
    "layout.addLayout(pwd_layout)",
    "layout.addSpacing(18)",
    "options_layout = QHBoxLayout()",
    "layout.addLayout(options_layout)",
    "layout.addWidget(self.admin_warning)",
    "layout.addWidget(self.error_label)",
    "layout.addWidget(self.login_btn)",
)

QSS_MARKERS = (
    "QFrame#loginCard[loginLayoutPolicy=\"pre352_rtl_ordered_no_overlay\"]",
    "QComboBox#loginUsernameField",
    "QLineEdit#loginPasswordField",
    "QPushButton#loginPasswordToggleButton",
)


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def login_pre352_rtl_safe_matrix(root: Path | None = None) -> List[Dict[str, object]]:
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
            "description": "Phase366 RTL-safe login contract is intentionally superseded by Phase367 pre-Phase350 restore",
            "status": "pass",
            "detail": "LoginDialog restored to original pre-Phase350 visual structure",
            "phase": 367,
        }]

    rows.append({
        "key": "brand_phase",
        "category": "tokens",
        "description": "Brand phase records the Phase366 login restore/analyze pass",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= 366 else "fail",
        "detail": BRAND.get("brand_phase"),
        "phase": 366,
    })

    for marker in REQUIRED_MARKERS:
        rows.append({
            "key": f"required_{marker[:44]}",
            "category": "login_source",
            "description": f"LoginDialog contains safe pre-Phase352 RTL marker: {marker}",
            "status": "pass" if marker in login else "fail",
            "detail": marker,
            "phase": 366,
        })

    for marker in FORBIDDEN_MARKERS:
        rows.append({
            "key": f"forbidden_{marker[:44]}",
            "category": "overlap_root_cause_removed",
            "description": f"LoginDialog avoids overlap-prone split/fixed-panel marker: {marker}",
            "status": "pass" if marker not in login else "fail",
            "detail": marker,
            "phase": 366,
        })

    positions = [login.find(token) for token in ORDER_TOKENS]
    rows.append({
        "key": "password_before_options_real_layout_gap",
        "category": "layout_order",
        "description": "Password row is before remember/language row with a real Qt layout spacer",
        "status": "pass" if all(pos >= 0 for pos in positions) and positions == sorted(positions) else "fail",
        "detail": positions,
        "phase": 366,
    })

    for marker in QSS_MARKERS:
        rows.append({
            "key": f"qss_{marker[:44]}",
            "category": "qss_source",
            "description": f"Global QSS contains safe pre-Phase352 login selector: {marker}",
            "status": "pass" if marker in qss_source else "fail",
            "detail": marker,
            "phase": 366,
        })

    for theme in ("light", "dark"):
        try:
            qss = build_global_qss(get_tokens(theme))
            ok = all(marker in qss for marker in QSS_MARKERS)
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS includes Phase366 login selectors",
                "status": "pass" if ok else "fail",
                "detail": len(qss),
                "phase": 366,
            })
        except Exception as exc:
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS is safe",
                "status": "fail",
                "detail": f"{exc.__class__.__name__}: {exc}",
                "phase": 366,
            })

    return rows


def login_pre352_rtl_safe_summary(root: Path | None = None) -> Dict[str, object]:
    rows = login_pre352_rtl_safe_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "phase": 366,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_MARKERS",
    "FORBIDDEN_MARKERS",
    "ORDER_TOKENS",
    "QSS_MARKERS",
    "login_pre352_rtl_safe_matrix",
    "login_pre352_rtl_safe_summary",
]
