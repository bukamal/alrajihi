# -*- coding: utf-8 -*-
"""Phase 368/431 contract: Login password visibility button alignment.

Phase431 makes the login dialog horizontal, but keeps the Phase368 rule: the
password visibility button is a fixed-size layout peer, never an overlay inside
or over the QLineEdit.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from theme.brand import BRAND, get_tokens
from theme.qss import build_global_qss

ROOT = Path(__file__).resolve().parents[3]
LOGIN_PATH = "alrajhi_client/views/dialogs/login_dialog.py"
QSS_PATH = "alrajhi_client/theme/qss.py"

PHASE368_MARKER = "Phase368: password visibility button is aligned as a separate fixed-size peer, never painted over the password field."

REQUIRED_ALIGNMENT_MARKERS = (
    PHASE368_MARKER,
    "Phase431: horizontal branded login layout",
    "pwd_row = QFrame()",
    "pwd_row.setObjectName('loginPasswordRow')",
    "pwd_layout = QHBoxLayout(pwd_row)",
    "pwd_layout.setSpacing(10)",
    "pwd_layout.setContentsMargins(0, 0, 0, 0)",
    "self.password_edit.setObjectName('loginPasswordEdit')",
    "self.password_edit.setMinimumHeight(int(BRAND.get('login_field_height', 48)))",
    "self.password_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)",
    "self.show_pwd_btn.setObjectName('loginPasswordVisibilityButton')",
    "self.show_pwd_btn.setFixedSize(42, 42)",
    "self.show_pwd_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)",
    "pwd_layout.addWidget(self.password_edit, 1)",
    "pwd_layout.addWidget(self.show_pwd_btn, 0, Qt.AlignVCenter)",
)

REQUIRED_QSS_MARKERS = (
    "QLineEdit#loginPasswordEdit",
    "QPushButton#loginPasswordVisibilityButton",
    "min-width: 42px;",
    "max-width: 42px;",
    "min-height: 42px;",
    "max-height: 42px;",
    "padding: 0px;",
    "margin: 0px;",
    "QFrame#loginCard[loginDensity=\"horizontal_compact\"] QFrame#loginPasswordRow",
)

FORBIDDEN_OVERLAY_MARKERS = (
    "setParent(self.password_edit)",
    "move(self.password_edit",
    "password_edit.addAction",
    "QLineEdit#loginPasswordEdit { padding-right: 42px",
    "QLineEdit#loginPasswordEdit { padding-left: 42px",
    "position: absolute",
    "loginPasswordSafeSpacer",
    "loginPasswordToggleButton",
)

ORDER_TOKENS = (
    "self.password_edit = QLineEdit()",
    "self.password_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)",
    "self.show_pwd_btn = QPushButton()",
    "self.show_pwd_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)",
    "pwd_layout.addWidget(self.password_edit, 1)",
    "pwd_layout.addWidget(self.show_pwd_btn, 0, Qt.AlignVCenter)",
    "credentials_layout.addWidget(pwd_row)",
    "self.options_panel = QFrame()",
)


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def login_password_toggle_alignment_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    login = _read(LOGIN_PATH, base)
    qss_source = _read(QSS_PATH, base)
    rows: List[Dict[str, object]] = []

    rows.append({
        "key": "brand_phase",
        "category": "tokens",
        "description": "Brand phase records the Phase431 horizontal login with Phase368 peer toggle rule",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= 431 else "fail",
        "detail": BRAND.get("brand_phase"),
        "phase": 431,
    })

    for marker in REQUIRED_ALIGNMENT_MARKERS:
        rows.append({
            "key": f"required_login_{marker[:44]}",
            "category": "login_source",
            "description": f"LoginDialog contains password toggle alignment marker: {marker}",
            "status": "pass" if marker in login else "fail",
            "detail": marker,
            "phase": 431,
        })

    for marker in REQUIRED_QSS_MARKERS:
        rows.append({
            "key": f"required_qss_{marker[:44]}",
            "category": "qss_source",
            "description": f"QSS fixes password toggle geometry: {marker}",
            "status": "pass" if marker in qss_source else "fail",
            "detail": marker,
            "phase": 431,
        })

    for marker in FORBIDDEN_OVERLAY_MARKERS:
        rows.append({
            "key": f"forbidden_{marker[:44]}",
            "category": "no_overlay_implementation",
            "description": f"Login password toggle avoids overlay/absolute geometry marker: {marker}",
            "status": "pass" if marker not in login else "fail",
            "detail": marker,
            "phase": 431,
        })

    positions = [login.find(token) for token in ORDER_TOKENS]
    rows.append({
        "key": "password_peer_layout_order",
        "category": "layout_order",
        "description": "Password field and visibility button are configured before insertion as fixed/expanding peers",
        "status": "pass" if all(pos >= 0 for pos in positions) and positions == sorted(positions) else "fail",
        "detail": positions,
        "phase": 431,
    })

    for theme in ("light", "dark"):
        try:
            qss = build_global_qss(get_tokens(theme))
            ok = all(marker in qss for marker in ("QLineEdit#loginPasswordEdit", "QPushButton#loginPasswordVisibilityButton", "max-width: 42px;", "loginPasswordRow"))
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS contains safe password toggle selectors",
                "status": "pass" if ok else "fail",
                "detail": len(qss),
                "phase": 431,
            })
        except Exception as exc:
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS is safe after password toggle alignment",
                "status": "fail",
                "detail": f"{exc.__class__.__name__}: {exc}",
                "phase": 431,
            })

    return rows


def login_password_toggle_alignment_summary(root: Path | None = None) -> Dict[str, object]:
    rows = login_password_toggle_alignment_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        category = str(row.get("category", "unknown"))
        categories[category] = categories.get(category, 0) + 1
    return {
        "phase": 431,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "PHASE368_MARKER",
    "REQUIRED_ALIGNMENT_MARKERS",
    "REQUIRED_QSS_MARKERS",
    "FORBIDDEN_OVERLAY_MARKERS",
    "ORDER_TOKENS",
    "login_password_toggle_alignment_matrix",
    "login_password_toggle_alignment_summary",
]
