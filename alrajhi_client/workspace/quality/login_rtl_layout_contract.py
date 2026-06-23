# -*- coding: utf-8 -*-
"""Phase 360 contract: organized RTL login layout.

The login screen keeps the Phase355 split identity design, but the active layout
is explicitly RTL-first: brand panel on the logical right for Arabic, form panel
on the logical left, right-aligned labels/fields, separated credentials/options/actions
sections, and short account-switch caption with the long localized text kept as tooltip.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from theme.brand import BRAND, get_tokens
from theme.qss import build_global_qss

ROOT = Path(__file__).resolve().parents[3]
LOGIN_PATH = "alrajhi_client/views/dialogs/login_dialog.py"
QSS_PATH = "alrajhi_client/theme/qss.py"

REQUIRED_LOGIN_RTL_MARKERS = (
    "Phase360: RTL-first organized login layout",
    "loginLayout', 'rtl_organized_split'",
    "root_layout = QHBoxLayout(self.content_widget)",
    "root_layout.addWidget(self.brand_panel, 0)",
    "root_layout.addWidget(self.form_panel, 1)",
    "QBoxLayout.RightToLeft if self._is_rtl() else QBoxLayout.LeftToRight",
    "self._apply_directional_layout()",
    "self._apply_switch_button_text()",
    "self.username_label = self._field_label(translate('username'))",
    "self.password_label = self._field_label(translate('password'))",
    "self.credentials_panel = QFrame()",
    "self.options_panel = QFrame()",
    "self.actions_panel = QFrame()",
    "self.switch_btn.setToolTip(translate('switch_account'))",
)

REQUIRED_QSS_MARKERS = (
    "QFrame#loginCredentialsPanel",
    "QFrame#loginOptionsPanel",
    "QFrame#loginActionsPanel",
    "QLabel#loginFieldLabel",
    "rtl_organized_split",
)

FORBIDDEN_OVERLAP_MARKERS = (
    "login_brand_header(",
    "QGridLayout(options_panel)",
    "loginLayout', 'stable_centered'",
    "QPushButton(translate('switch_account'))\n        self.switch_btn.clicked.connect",
)


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding="utf-8")


def login_rtl_layout_matrix(root: Path | None = None) -> List[Dict[str, object]]:
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
            "description": "Phase 360 login-specific layout contract is intentionally superseded by Phase365 Phase352 restore",
            "status": "pass",
            "detail": "LoginDialog restored to Phase352 single-card visual structure",
            "phase": 360,
        }]
    qss_source = _read(QSS_PATH, base)
    rows: List[Dict[str, object]] = []

    rows.append({
        "key": "brand_phase",
        "category": "tokens",
        "description": "Brand system is still active after login RTL reflow",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= 358 else "fail",
        "detail": BRAND.get("brand_phase"),
        "phase": 360,
    })

    for marker in REQUIRED_LOGIN_RTL_MARKERS:
        rows.append({
            "key": f"login_{marker[:44]}",
            "category": "login_source",
            "description": f"LoginDialog includes RTL organized marker: {marker}",
            "status": "pass" if marker in login else "fail",
            "detail": marker,
            "phase": 360,
        })

    for marker in REQUIRED_QSS_MARKERS:
        rows.append({
            "key": f"qss_{marker[:44]}",
            "category": "qss_source",
            "description": f"QSS contains RTL organized login selector: {marker}",
            "status": "pass" if marker in qss_source else "fail",
            "detail": marker,
            "phase": 360,
        })

    for marker in FORBIDDEN_OVERLAP_MARKERS:
        rows.append({
            "key": f"forbid_{marker[:44]}",
            "category": "overlap_prevention",
            "description": f"Login layout avoids known overlap marker: {marker}",
            "status": "pass" if marker not in login else "fail",
            "detail": marker,
            "phase": 360,
        })

    for theme in ("light", "dark"):
        try:
            qss = build_global_qss(get_tokens(theme))
            ok = all(marker in qss for marker in ("QFrame#loginCredentialsPanel", "QLabel#loginFieldLabel"))
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS includes organized login selectors",
                "status": "pass" if ok else "fail",
                "detail": len(qss),
                "phase": 360,
            })
        except Exception as exc:
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS is safe",
                "status": "fail",
                "detail": f"{exc.__class__.__name__}: {exc}",
                "phase": 360,
            })

    return rows


def login_rtl_layout_summary(root: Path | None = None) -> Dict[str, object]:
    rows = login_rtl_layout_matrix(root)
    issues = [row for row in rows if row.get("status") != "pass"]
    categories: Dict[str, int] = {}
    for row in rows:
        cat = str(row.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
    return {
        "phase": 360,
        "checks": len(rows),
        "issues": len(issues),
        "issue_groups": len({row.get("category") for row in issues}),
        "categories": categories,
        "ready": not issues,
    }


__all__ = [
    "REQUIRED_LOGIN_RTL_MARKERS",
    "REQUIRED_QSS_MARKERS",
    "FORBIDDEN_OVERLAP_MARKERS",
    "login_rtl_layout_matrix",
    "login_rtl_layout_summary",
]
