# -*- coding: utf-8 -*-
"""Phase 433 contract: horizontal login password row visibility fix."""
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
    "Phase433: password-row-visible horizontal login form",
    "self.main_frame.setProperty('loginPasswordPolicy', 'password_row_visible_fixed')",
    "form_layout.setSizeConstraint(QLayout.SetMinimumSize)",
    "credentials_layout.setSizeConstraint(QLayout.SetMinimumSize)",
    "self.credentials_panel.setMinimumHeight(int(BRAND.get('login_credentials_runtime_fixed_height', 246)))",
    "self.password_row = QFrame()",
    "self.password_row.setObjectName('loginPasswordRow')",
    "self.password_row.setProperty('loginPasswordRowPolicy', 'visible_fixed')",
    "self.password_row.setMinimumHeight(int(BRAND.get('login_password_runtime_row_height', 58)))",
    "self.password_edit.setObjectName('loginPasswordEdit')",
    "self.password_edit.setVisible(True)",
    "credentials_layout.addWidget(self.password_row)",
    "self._enforce_password_row_visibility_contract()",
    "def _enforce_password_row_visibility_contract(self):",
    "self.password_row.setVisible(True)",
    "self.show_pwd_btn.setVisible(True)",
)

ORDER_MARKERS = (
    "self.username_combo = QComboBox()",
    "self.password_label = QLabel(translate('password'))",
    "self.password_row = QFrame()",
    "credentials_layout.addWidget(self.password_row)",
    "self._enforce_password_row_visibility_contract()",
    "self.options_panel = QFrame()",
)

REQUIRED_TOKEN_KEYS = (
    "login_credentials_runtime_fixed_height",
    "login_credentials_runtime_max_height",
    "login_password_runtime_row_height",
    "login_password_runtime_row_max_height",
    "login_password_runtime_field_height",
    "login_password_runtime_field_max_height",
    "login_password_runtime_button_size",
)

MINIMUM_TOKEN_VALUES = {
    "login_credentials_runtime_fixed_height": 230,
    "login_credentials_runtime_max_height": 260,
    "login_password_runtime_row_height": 54,
    "login_password_runtime_field_height": 44,
    "login_password_runtime_button_size": 40,
}

REQUIRED_QSS_MARKERS = (
    "Phase433: password row visible fix",
    "loginPasswordPolicy=\"password_row_visible_fixed\"",
    "QFrame#loginPasswordRow",
    "QLineEdit#loginPasswordEdit",
    "QPushButton#loginPasswordVisibilityButton",
    "QFrame#loginOptionsPanel",
)

FORBIDDEN_MARKERS = (
    "credentials_layout.addWidget(pwd_row)",
    "pwd_row = QFrame()",
)


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def _in_order(source: str, markers: tuple[str, ...]) -> bool:
    pos = -1
    for marker in markers:
        nxt = source.find(marker, pos + 1)
        if nxt < 0:
            return False
        pos = nxt
    return True


def login_password_row_visibility_fix_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    login = _read(LOGIN_PATH, base)
    brand = _read(BRAND_PATH, base)
    qss_source = _read(QSS_PATH, base)
    rows: List[Dict[str, object]] = []

    rows.append({
        "key": "brand_phase_433",
        "category": "tokens",
        "description": "BRAND phase records password row visibility fix",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= 433 else "fail",
        "detail": BRAND.get("brand_phase"),
    })

    for marker in REQUIRED_LOGIN_MARKERS:
        rows.append({
            "key": f"login_required_{marker[:45]}",
            "category": "login_source",
            "description": f"LoginDialog contains Phase433 marker: {marker}",
            "status": "pass" if marker in login else "fail",
            "detail": marker,
        })

    rows.append({
        "key": "login_password_before_options_order",
        "category": "login_source_order",
        "description": "Password input row is constructed and added before language/remember options",
        "status": "pass" if _in_order(login, ORDER_MARKERS) else "fail",
        "detail": ORDER_MARKERS,
    })

    for marker in FORBIDDEN_MARKERS:
        rows.append({
            "key": f"forbidden_{marker[:45]}",
            "category": "legacy_layout_removed",
            "description": f"Legacy local password row marker removed: {marker}",
            "status": "pass" if marker not in login else "fail",
            "detail": marker,
        })

    for key in REQUIRED_TOKEN_KEYS:
        rows.append({
            "key": f"token_{key}",
            "category": "tokens",
            "description": f"BRAND defines Phase433 token {key}",
            "status": "pass" if key in BRAND and key in brand else "fail",
            "detail": {"key": key, "value": BRAND.get(key)},
        })

    for key, minimum in MINIMUM_TOKEN_VALUES.items():
        rows.append({
            "key": f"token_min_{key}",
            "category": "token_values",
            "description": f"{key} is large enough to keep password field visible",
            "status": "pass" if int(BRAND.get(key, 0)) >= minimum else "fail",
            "detail": {"actual": BRAND.get(key), "minimum": minimum},
        })

    for marker in REQUIRED_QSS_MARKERS:
        rows.append({
            "key": f"qss_{marker[:45]}",
            "category": "qss_source",
            "description": f"QSS contains password-row visibility marker: {marker}",
            "status": "pass" if marker in qss_source else "fail",
            "detail": marker,
        })

    for theme in ("light", "dark"):
        try:
            qss = build_global_qss(get_tokens(theme))
            ok = all(marker in qss for marker in ("Phase433", "loginPasswordPolicy=\"password_row_visible_fixed\"", "QLineEdit#loginPasswordEdit"))
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS contains Phase433 password row rules",
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


def login_password_row_visibility_fix_summary(root: Path | None = None) -> Dict[str, object]:
    rows = login_password_row_visibility_fix_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        category = str(row.get("category", "unknown"))
        categories[category] = categories.get(category, 0) + 1
    return {
        "phase": 433,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_LOGIN_MARKERS",
    "ORDER_MARKERS",
    "REQUIRED_TOKEN_KEYS",
    "REQUIRED_QSS_MARKERS",
    "FORBIDDEN_MARKERS",
    "MINIMUM_TOKEN_VALUES",
    "login_password_row_visibility_fix_matrix",
    "login_password_row_visibility_fix_summary",
]
