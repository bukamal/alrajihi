# -*- coding: utf-8 -*-
"""Phase 432 contract: runtime-stabilized horizontal branded login.

The horizontal login surface must be a real desktop split layout, not a narrow
vertical dialog stretched sideways.  The contract checks the source-level
runtime safeguards that prevent the specific defects seen in the screenshot:
large tab-like title buttons, compressed form panels, unreadable brand labels,
empty red error bar, and options/password overlap.
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
    "Phase432: runtime-stabilized horizontal login layout",
    "self.resize(int(BRAND.get('login_horizontal_width', 1120)), int(BRAND.get('login_horizontal_height', 660)))",
    "self.setMinimumSize(int(BRAND.get('login_horizontal_min_width', 980)), int(BRAND.get('login_horizontal_min_height', 600)))",
    "self.main_frame.setProperty('loginRuntimePolicy', 'horizontal_runtime_stabilized')",
    "self._stabilize_horizontal_login_chrome()",
    "self.title_bar.setObjectName('LoginRuntimeTitleBar')",
    "self.title_bar.setFixedHeight(int(BRAND.get('login_runtime_titlebar_height', 40)))",
    "self.title_label.setObjectName('LoginRuntimeTitle')",
    "self.icon_label.setVisible(False)",
    "'LoginRuntimeCloseButton'",
    "'LoginRuntimeMinButton'",
    "btn.setFixedSize(30, 30)",
    "self.brand_panel.setMinimumHeight(int(BRAND.get('login_horizontal_panel_min_height', 540)))",
    "self.form_panel.setMinimumHeight(int(BRAND.get('login_horizontal_panel_min_height', 540)))",
    "self.options_panel.setMinimumHeight(int(BRAND.get('login_options_runtime_height', 54)))",
    "self.admin_warning.setMinimumHeight(int(BRAND.get('login_warning_reserved_height', 30)))",
    "self.error_label.setObjectName('loginRuntimeMessage')",
    "self.error_label.setProperty('messageState', 'empty')",
    "self.error_label.setMinimumHeight(int(BRAND.get('login_message_reserved_height', 34)))",
    "self.error_label.setProperty('messageState', 'danger')",
    "self.error_label.setProperty('messageState', 'success')",
)

REQUIRED_TOKEN_KEYS = (
    "login_horizontal_width",
    "login_horizontal_height",
    "login_horizontal_min_width",
    "login_horizontal_min_height",
    "login_horizontal_brand_width",
    "login_horizontal_form_width",
    "login_horizontal_panel_min_height",
    "login_runtime_titlebar_height",
    "login_options_runtime_height",
    "login_options_runtime_max_height",
    "login_warning_reserved_height",
    "login_warning_reserved_max_height",
    "login_message_reserved_height",
    "login_message_reserved_max_height",
)

REQUIRED_QSS_MARKERS = (
    "Phase432: runtime-stabilized horizontal login chrome",
    "LoginRuntimeTitleBar",
    "LoginRuntimeTitle",
    "LoginRuntimeCloseButton",
    "LoginRuntimeMinButton",
    "loginRuntimePolicy=\"horizontal_runtime_stabilized\"",
    "QLabel#loginRuntimeMessage",
    "messageState=\"danger\"",
    "messageState=\"success\"",
    "QFrame#loginCredentialsPanel",
    "QFrame#loginOptionsPanel",
    "QLabel#loginAdminWarning",
    "background: transparent",
)

FORBIDDEN_RUNTIME_MARKERS = (
    "self.resize(int(BRAND.get('login_horizontal_width', 1040)), int(BRAND.get('login_horizontal_height', 640)))",
    "self.setMinimumSize(int(BRAND.get('login_horizontal_min_width', 900)), int(BRAND.get('login_horizontal_min_height', 560)))",
    "self.error_label.setObjectName('danger')",
)

MINIMUM_TOKEN_VALUES = {
    "login_horizontal_width": 1100,
    "login_horizontal_height": 650,
    "login_horizontal_min_width": 960,
    "login_horizontal_min_height": 590,
    "login_horizontal_brand_width": 380,
    "login_horizontal_form_width": 600,
    "login_horizontal_panel_min_height": 530,
    "login_runtime_titlebar_height": 36,
}


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def horizontal_login_runtime_stabilization_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    login = _read(LOGIN_PATH, base)
    brand = _read(BRAND_PATH, base)
    qss_source = _read(QSS_PATH, base)
    rows: List[Dict[str, object]] = []

    rows.append({
        "key": "brand_phase_432",
        "category": "tokens",
        "description": "BRAND phase records runtime-stabilized horizontal login work",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= 432 else "fail",
        "detail": BRAND.get("brand_phase"),
    })

    for marker in REQUIRED_LOGIN_MARKERS:
        rows.append({
            "key": f"login_required_{marker[:42]}",
            "category": "login_source",
            "description": f"LoginDialog contains Phase432 runtime marker: {marker}",
            "status": "pass" if marker in login else "fail",
            "detail": marker,
        })

    for marker in FORBIDDEN_RUNTIME_MARKERS:
        rows.append({
            "key": f"login_forbid_{marker[:42]}",
            "category": "legacy_runtime_removed",
            "description": f"LoginDialog no longer uses unstable runtime marker: {marker}",
            "status": "pass" if marker not in login else "fail",
            "detail": marker,
        })

    for key in REQUIRED_TOKEN_KEYS:
        rows.append({
            "key": f"token_{key}",
            "category": "tokens",
            "description": f"BRAND defines Phase432 token {key}",
            "status": "pass" if key in BRAND and key in brand else "fail",
            "detail": key,
        })

    for key, minimum in MINIMUM_TOKEN_VALUES.items():
        rows.append({
            "key": f"token_min_{key}",
            "category": "token_values",
            "description": f"{key} is large enough for desktop horizontal login runtime",
            "status": "pass" if int(BRAND.get(key, 0)) >= minimum else "fail",
            "detail": {"actual": BRAND.get(key), "minimum": minimum},
        })

    for marker in REQUIRED_QSS_MARKERS:
        rows.append({
            "key": f"qss_{marker[:42]}",
            "category": "qss_source",
            "description": f"QSS contains Phase432 runtime selector/marker: {marker}",
            "status": "pass" if marker in qss_source else "fail",
            "detail": marker,
        })

    for theme in ("light", "dark"):
        try:
            qss = build_global_qss(get_tokens(theme))
            ok = all(marker in qss for marker in ("Phase432", "LoginRuntimeTitleBar", "QLabel#loginRuntimeMessage", "messageState=\"danger\""))
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS includes Phase432 runtime stabilization",
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


def horizontal_login_runtime_stabilization_summary(root: Path | None = None) -> Dict[str, object]:
    rows = horizontal_login_runtime_stabilization_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        category = str(row.get("category", "unknown"))
        categories[category] = categories.get(category, 0) + 1
    return {
        "phase": 432,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_LOGIN_MARKERS",
    "REQUIRED_TOKEN_KEYS",
    "REQUIRED_QSS_MARKERS",
    "FORBIDDEN_RUNTIME_MARKERS",
    "MINIMUM_TOKEN_VALUES",
    "horizontal_login_runtime_stabilization_matrix",
    "horizontal_login_runtime_stabilization_summary",
]
