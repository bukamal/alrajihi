# -*- coding: utf-8 -*-
"""Phase 433 login password row visibility tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.login_password_row_visibility_fix_contract import (  # noqa: E402
    FORBIDDEN_MARKERS,
    ORDER_MARKERS,
    REQUIRED_LOGIN_MARKERS,
    REQUIRED_QSS_MARKERS,
    REQUIRED_TOKEN_KEYS,
    login_password_row_visibility_fix_summary,
)


def _login_source() -> str:
    return (ROOT / "alrajhi_client" / "views" / "dialogs" / "login_dialog.py").read_text(encoding="utf-8")


def _qss_source() -> str:
    return (ROOT / "alrajhi_client" / "theme" / "qss.py").read_text(encoding="utf-8")


def test_phase433_login_markers_present():
    source = _login_source()
    for marker in REQUIRED_LOGIN_MARKERS:
        assert marker in source


def test_phase433_password_row_before_options():
    source = _login_source()
    pos = -1
    for marker in ORDER_MARKERS:
        nxt = source.find(marker, pos + 1)
        assert nxt >= 0, marker
        pos = nxt


def test_phase433_legacy_local_password_row_removed():
    source = _login_source()
    for marker in FORBIDDEN_MARKERS:
        assert marker not in source


def test_phase433_tokens_ready():
    from theme.brand import BRAND

    for key in REQUIRED_TOKEN_KEYS:
        assert key in BRAND
    assert int(BRAND["login_credentials_runtime_fixed_height"]) >= 230
    assert int(BRAND["login_password_runtime_row_height"]) >= 54
    assert int(BRAND["login_password_runtime_field_height"]) >= 44


def test_phase433_qss_markers_present():
    qss = _qss_source()
    for marker in REQUIRED_QSS_MARKERS:
        assert marker in qss


def test_phase433_guard_summary_ready():
    summary = login_password_row_visibility_fix_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 30
