# -*- coding: utf-8 -*-
"""Phase 367 compatibility contract, superseded by Phase431 horizontal login.

Phase431 intentionally replaces the old narrow vertical LoginDialog with a
horizontal branded split surface. This module remains for older tests/guards and
now validates that the legacy vertical restore is no longer the active target.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from theme.brand import BRAND, get_tokens
from theme.qss import build_global_qss

ROOT = Path(__file__).resolve().parents[3]
LOGIN_PATH = "alrajhi_client/views/dialogs/login_dialog.py"
QSS_PATH = "alrajhi_client/theme/qss.py"

PHASE367_MARKER = "Phase431: horizontal branded login layout"

REQUIRED_PRE350_MARKERS = (
    PHASE367_MARKER,
    "self.resize(int(BRAND.get('login_horizontal_width', 1040)), int(BRAND.get('login_horizontal_height', 640)))",
    "self.setMinimumSize(int(BRAND.get('login_horizontal_min_width', 900)), int(BRAND.get('login_horizontal_min_height', 560)))",
    "self.main_frame.setObjectName('loginCard')",
    "self.main_frame.setProperty('loginLayout', 'horizontal_branded_split')",
    "self.main_frame.setProperty('loginLayoutPolicy', 'horizontal_brand_form_no_overlay')",
    "root_layout = QHBoxLayout(self.content_widget)",
    "self.brand_panel = brand_side_panel(",
    "self.form_panel = first_run_form_panel()",
    "self.credentials_panel = QFrame()",
    "self.options_panel = QFrame()",
    "pwd_layout = QHBoxLayout(pwd_row)",
    "pwd_layout.addWidget(self.password_edit, 1)",
    "pwd_layout.addWidget(self.show_pwd_btn, 0, Qt.AlignVCenter)",
    "set_first_run_primary(self.login_btn)",
    "set_first_run_secondary(self.switch_btn)",
)

FORBIDDEN_REDESIGN_MARKERS = (
    "layout = QVBoxLayout(self.content_widget)",
    "self.resize(500, 620)",
    "self.setMinimumSize(430, 540)",
    "self.app_title_label.setObjectName(\"heroTitle\")",
    "self.subtitle_label.setObjectName('muted')",
    "layout.addLayout(pwd_layout)",
    "layout.addLayout(options_layout)",
    "self.login_btn.setObjectName(\"primary\")",
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
)

QSS_RUNTIME_MARKERS = (
    "QFrame#loginCard",
    "horizontal_branded_split",
    "QFrame#firstRunBrandPanel",
    "QFrame#firstRunFormPanel",
    "QLabel#firstRunFormTitle",
    "QPushButton#firstRunPrimary",
)


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def login_pre350_restore_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    login = _read(LOGIN_PATH, base)
    qss_source = _read(QSS_PATH, base)
    rows: List[Dict[str, object]] = []

    rows.append({
        "key": "brand_phase",
        "category": "tokens",
        "description": "Brand phase records the Phase431 horizontal branded login supersession",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= 431 else "fail",
        "detail": BRAND.get("brand_phase"),
        "phase": 431,
    })

    for marker in REQUIRED_PRE350_MARKERS:
        rows.append({
            "key": f"required_{marker[:50]}",
            "category": "login_source",
            "description": f"LoginDialog contains Phase431 horizontal marker: {marker}",
            "status": "pass" if marker in login else "fail",
            "detail": marker,
            "phase": 431,
        })

    for marker in FORBIDDEN_REDESIGN_MARKERS:
        rows.append({
            "key": f"forbidden_{marker[:50]}",
            "category": "vertical_legacy_removed",
            "description": f"LoginDialog no longer uses narrow vertical marker: {marker}",
            "status": "pass" if marker not in login else "fail",
            "detail": marker,
            "phase": 431,
        })

    positions = [login.find(token) for token in ORDER_TOKENS]
    rows.append({
        "key": "horizontal_order",
        "category": "layout_order",
        "description": "Horizontal login builds shell, brand panel, form panel, credentials, options and actions in stable order",
        "status": "pass" if all(pos >= 0 for pos in positions) and positions == sorted(positions) else "fail",
        "detail": positions,
        "phase": 431,
    })

    for marker in QSS_RUNTIME_MARKERS:
        rows.append({
            "key": f"qss_source_{marker[:32]}",
            "category": "qss_source",
            "description": f"Global QSS supports Phase431 horizontal login selector: {marker}",
            "status": "pass" if marker in qss_source else "fail",
            "detail": marker,
            "phase": 431,
        })

    for theme in ("light", "dark"):
        try:
            qss = build_global_qss(get_tokens(theme))
            ok = all(marker in qss for marker in QSS_RUNTIME_MARKERS)
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS supports Phase431 horizontal login",
                "status": "pass" if ok else "fail",
                "detail": len(qss),
                "phase": 431,
            })
        except Exception as exc:
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS is safe for LoginDialog",
                "status": "fail",
                "detail": f"{exc.__class__.__name__}: {exc}",
                "phase": 431,
            })

    return rows


def login_pre350_restore_summary(root: Path | None = None) -> Dict[str, object]:
    rows = login_pre350_restore_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "phase": 431,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "PHASE367_MARKER",
    "REQUIRED_PRE350_MARKERS",
    "FORBIDDEN_REDESIGN_MARKERS",
    "ORDER_TOKENS",
    "QSS_RUNTIME_MARKERS",
    "login_pre350_restore_matrix",
    "login_pre350_restore_summary",
]
