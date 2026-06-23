# -*- coding: utf-8 -*-
"""Phase 367 contract: restore LoginDialog visual design to the pre-Phase350 baseline.

This contract intentionally rejects the Phase352+ login redesign experiments for
LoginDialog only.  The original screen is a single centered card with a direct
QVBoxLayout, one password QHBoxLayout, and one remember/language QHBoxLayout.
The root cause of the later overlap was nested branded panels, fixed-height
sections, and QSS-only margins competing with Qt's geometry calculation.  The
safe restore removes those layout constructs from the login dialog.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from theme.brand import BRAND, get_tokens
from theme.qss import build_global_qss

ROOT = Path(__file__).resolve().parents[3]
LOGIN_PATH = "alrajhi_client/views/dialogs/login_dialog.py"
QSS_PATH = "alrajhi_client/theme/qss.py"

PHASE367_MARKER = "Phase367: restored LoginDialog visual structure to the pre-Phase350 original baseline."

REQUIRED_PRE350_MARKERS = (
    PHASE367_MARKER,
    "self.resize(500, 620)",
    "self.setMinimumSize(430, 540)",
    "self.main_frame.setObjectName('loginCard')",
    "layout = QVBoxLayout(self.content_widget)",
    "layout.setSpacing(14)",
    "layout.setContentsMargins(34, 24, 34, 30)",
    "logo.setPixmap(QPixmap(logo_png(128)).scaled(94, 94, Qt.KeepAspectRatio, Qt.SmoothTransformation))",
    "self.app_title_label.setObjectName(\"heroTitle\")",
    "self.subtitle_label.setObjectName('muted')",
    "self.username_combo = QComboBox()",
    "self.username_combo.setEditable(True)",
    "self.username_combo.setPlaceholderText(translate('username'))",
    "pwd_layout = QHBoxLayout()",
    "self.password_edit = QLineEdit()",
    "self.password_edit.setPlaceholderText(translate('password'))",
    "self.show_pwd_btn.setFixedSize(42, 42)",
    "pwd_layout.addWidget(self.password_edit)",
    "pwd_layout.addWidget(self.show_pwd_btn)",
    "layout.addLayout(pwd_layout)",
    "options_layout = QHBoxLayout()",
    "options_layout.addWidget(self.remember_check)",
    "options_layout.addStretch()",
    "self.lang_combo.setFixedWidth(128)",
    "layout.addLayout(options_layout)",
    "self.login_btn.setObjectName(\"primary\")",
    "self.switch_btn = DesignSystem.secondary_button(translate('switch_account'))",
)

FORBIDDEN_REDESIGN_MARKERS = (
    "from ui.first_run_branding import",
    "brand_side_panel(",
    "first_run_form_panel(",
    "set_first_run_primary",
    "root_layout = QHBoxLayout(self.content_widget)",
    "self.brand_panel =",
    "self.form_panel =",
    "logo.setObjectName('brandMark')",
    "self.main_frame.setProperty('loginLayoutPolicy'",
    "self.main_frame.setProperty('loginLayout'",
    "self.main_frame.setProperty('loginDensity'",
    "self.main_frame.setProperty('loginOverlapPolicy'",
    "self.main_frame.setProperty('loginSpacingPolicy'",
    "loginCredentialsPanel",
    "loginOptionsPanel",
    "loginPasswordRow",
    "loginPasswordSafeSpacer",
    "loginUsernameField",
    "loginPasswordField",
    "loginLanguageField",
    "loginPasswordToggleButton",
    "self.username_label =",
    "self.password_label =",
    "def _field_label(self, text):",
    "def _apply_directional_alignment(self):",
)

ORDER_TOKENS = (
    "self.username_combo = QComboBox()",
    "layout.addWidget(self.username_combo)",
    "pwd_layout = QHBoxLayout()",
    "layout.addLayout(pwd_layout)",
    "options_layout = QHBoxLayout()",
    "layout.addLayout(options_layout)",
    "layout.addWidget(self.admin_warning)",
    "layout.addWidget(self.error_label)",
    "layout.addWidget(self.login_btn)",
    "layout.addWidget(self.switch_btn)",
)

QSS_RUNTIME_MARKERS = (
    "QFrame#loginCard",
    "QLabel#heroTitle",
    "QPushButton#primary",
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
        "description": "Brand phase records the Phase367 pre-Phase350 login restore",
        "status": "pass" if int(BRAND.get("brand_phase", 0)) >= 367 else "fail",
        "detail": BRAND.get("brand_phase"),
        "phase": 367,
    })

    for marker in REQUIRED_PRE350_MARKERS:
        rows.append({
            "key": f"required_{marker[:50]}",
            "category": "login_source",
            "description": f"LoginDialog contains original pre-Phase350 marker: {marker}",
            "status": "pass" if marker in login else "fail",
            "detail": marker,
            "phase": 367,
        })

    for marker in FORBIDDEN_REDESIGN_MARKERS:
        rows.append({
            "key": f"forbidden_{marker[:50]}",
            "category": "redesign_removed",
            "description": f"LoginDialog avoids post-Phase350 redesign/overlap marker: {marker}",
            "status": "pass" if marker not in login else "fail",
            "detail": marker,
            "phase": 367,
        })

    positions = [login.find(token) for token in ORDER_TOKENS]
    rows.append({
        "key": "original_vertical_order",
        "category": "layout_order",
        "description": "Original username -> password -> options -> warning -> actions order is restored",
        "status": "pass" if all(pos >= 0 for pos in positions) and positions == sorted(positions) else "fail",
        "detail": positions,
        "phase": 367,
    })

    for marker in QSS_RUNTIME_MARKERS:
        rows.append({
            "key": f"qss_source_{marker[:32]}",
            "category": "qss_source",
            "description": f"Global QSS still provides base selector required by original login design: {marker}",
            "status": "pass" if marker in qss_source else "fail",
            "detail": marker,
            "phase": 367,
        })

    for theme in ("light", "dark"):
        try:
            qss = build_global_qss(get_tokens(theme))
            ok = all(marker in qss for marker in QSS_RUNTIME_MARKERS)
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS supports original login selectors",
                "status": "pass" if ok else "fail",
                "detail": len(qss),
                "phase": 367,
            })
        except Exception as exc:
            rows.append({
                "key": f"qss_runtime_{theme}",
                "category": "qss_runtime",
                "description": f"Generated {theme} QSS is safe for LoginDialog",
                "status": "fail",
                "detail": f"{exc.__class__.__name__}: {exc}",
                "phase": 367,
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
        "phase": 367,
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
