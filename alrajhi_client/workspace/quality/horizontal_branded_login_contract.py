# -*- coding: utf-8 -*-
"""Phase 431 contract: horizontal branded LoginDialog layout.

The login surface must not be the old tall/narrow vertical card. It must be a
wide split surface using the project visual identity: brand panel on one side,
focused credentials form on the other, safe RTL/LTR text refresh and no local
change to authentication semantics.
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
    "Phase431: horizontal branded login layout",
    "self.resize(int(BRAND.get('login_horizontal_width', 1120)), int(BRAND.get('login_horizontal_height', 660)))",
    "self.setMinimumSize(int(BRAND.get('login_horizontal_min_width', 980)), int(BRAND.get('login_horizontal_min_height', 600)))",
    "self.main_frame.setProperty('loginLayout', 'horizontal_branded_split')",
    "self.main_frame.setProperty('loginLayoutPolicy', 'horizontal_brand_form_no_overlay')",
    "self.main_frame.setProperty('loginDensity', 'horizontal_compact')",
    "root_layout = QHBoxLayout(self.content_widget)",
    "root_layout.setContentsMargins(28, 24, 28, 30)",
    "self.brand_panel = brand_side_panel(",
    "self.form_panel = first_run_form_panel()",
    "self.credentials_panel = QFrame()",
    "self.options_panel = QFrame()",
    "self.username_label = QLabel(translate('username'))",
    "self.password_label = QLabel(translate('password'))",
    "self._refresh_brand_panel_texts()",
    "set_first_run_primary(self.login_btn)",
    "set_first_run_secondary(self.switch_btn)",
)

FORBIDDEN_VERTICAL_MARKERS = (
    "self.resize(500, 620)",
    "self.setMinimumSize(430, 540)",
    "layout = QVBoxLayout(self.content_widget)",
    "layout.setContentsMargins(34, 24, 34, 30)",
    "logo.setPixmap(QPixmap(logo_png(128)).scaled(94, 94",
    "layout.addWidget(logo)",
    "self.app_title_label.setObjectName(\"heroTitle\")",
    "self.subtitle_label.setObjectName('muted')",
    "self.login_btn.setObjectName(\"primary\")",
    "self.switch_btn = DesignSystem.secondary_button(translate('switch_account'))",
)

REQUIRED_TOKEN_KEYS = (
    "login_horizontal_width",
    "login_horizontal_height",
    "login_horizontal_min_width",
    "login_horizontal_min_height",
    "login_horizontal_brand_width",
    "login_horizontal_form_width",
)

REQUIRED_QSS_MARKERS = (
    "Phase431: horizontal branded login layout",
    "horizontal_branded_split",
    "horizontal_brand_form_no_overlay",
    "horizontal_compact",
    "QFrame#firstRunBrandPanel",
    "QFrame#firstRunFormPanel",
    "QLabel#firstRunFormTitle",
    "QFrame#loginPasswordRow",
)

ORDER_TOKENS = (
    "root_layout = QHBoxLayout(self.content_widget)",
    "self.brand_panel = brand_side_panel(",
    "self.form_panel = first_run_form_panel()",
    "self.credentials_panel = QFrame()",
    "self.username_combo = QComboBox()",
    "self.password_edit = QLineEdit()",
    "self.options_panel = QFrame()",
    "self.login_btn = QPushButton(translate('login'))",
    "self.switch_btn = QPushButton(translate('switch_account'))",
    "self._load_saved_user()",
)


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def horizontal_branded_login_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    login = _read(LOGIN_PATH, base)
    brand = _read(BRAND_PATH, base)
    qss_source = _read(QSS_PATH, base)
    rows: List[Dict[str, object]] = []

    rows.append({
        "key": "brand_phase",
        "category": "tokens",
        "description": "BRAND phase records horizontal login work",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= 431 else "fail",
        "detail": BRAND.get("brand_phase"),
    })

    for marker in REQUIRED_LOGIN_MARKERS:
        rows.append({
            "key": f"login_required_{marker[:42]}",
            "category": "login_source",
            "description": f"LoginDialog contains horizontal login marker: {marker}",
            "status": "pass" if marker in login else "fail",
            "detail": marker,
        })

    for marker in FORBIDDEN_VERTICAL_MARKERS:
        rows.append({
            "key": f"login_forbid_{marker[:42]}",
            "category": "vertical_legacy_removed",
            "description": f"LoginDialog no longer uses narrow vertical marker: {marker}",
            "status": "pass" if marker not in login else "fail",
            "detail": marker,
        })

    for key in REQUIRED_TOKEN_KEYS:
        rows.append({
            "key": f"token_{key}",
            "category": "tokens",
            "description": f"BRAND defines horizontal login token {key}",
            "status": "pass" if key in BRAND and key in brand else "fail",
            "detail": key,
        })

    for marker in REQUIRED_QSS_MARKERS:
        rows.append({
            "key": f"qss_{marker[:42]}",
            "category": "qss_source",
            "description": f"QSS contains horizontal login selector/marker: {marker}",
            "status": "pass" if marker in qss_source else "fail",
            "detail": marker,
        })

    positions = [login.find(token) for token in ORDER_TOKENS]
    rows.append({
        "key": "horizontal_layout_order",
        "category": "layout_order",
        "description": "Login builds horizontal shell, brand panel, form, credentials, options and actions in stable order",
        "status": "pass" if all(pos >= 0 for pos in positions) and positions == sorted(positions) else "fail",
        "detail": positions,
    })

    for theme in ("light", "dark"):
        try:
            qss = build_global_qss(get_tokens(theme))
            ok = all(marker in qss for marker in ("horizontal_branded_split", "QFrame#firstRunBrandPanel", "QFrame#firstRunFormPanel", "QFrame#loginPasswordRow"))
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS supports horizontal branded login",
                "status": "pass" if ok else "fail",
                "detail": len(qss),
            })
        except Exception as exc:
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS is safe for horizontal login",
                "status": "fail",
                "detail": f"{exc.__class__.__name__}: {exc}",
            })

    return rows


def horizontal_branded_login_summary(root: Path | None = None) -> Dict[str, object]:
    rows = horizontal_branded_login_matrix(root)
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
    "FORBIDDEN_VERTICAL_MARKERS",
    "REQUIRED_TOKEN_KEYS",
    "REQUIRED_QSS_MARKERS",
    "ORDER_TOKENS",
    "horizontal_branded_login_matrix",
    "horizontal_branded_login_summary",
]
