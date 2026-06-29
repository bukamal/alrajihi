# -*- coding: utf-8 -*-
"""Phase 431 horizontal branded LoginDialog tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.horizontal_branded_login_contract import (  # noqa: E402
    FORBIDDEN_VERTICAL_MARKERS,
    ORDER_TOKENS,
    REQUIRED_LOGIN_MARKERS,
    REQUIRED_QSS_MARKERS,
    REQUIRED_TOKEN_KEYS,
    horizontal_branded_login_summary,
)


def _login_source() -> str:
    return (ROOT / "alrajhi_client" / "views" / "dialogs" / "login_dialog.py").read_text(encoding="utf-8")


def _qss_source() -> str:
    return (ROOT / "alrajhi_client" / "theme" / "qss.py").read_text(encoding="utf-8")


def test_phase431_horizontal_login_markers_present():
    source = _login_source()
    for marker in REQUIRED_LOGIN_MARKERS:
        assert marker in source


def test_phase431_vertical_login_markers_removed():
    source = _login_source()
    for marker in FORBIDDEN_VERTICAL_MARKERS:
        assert marker not in source


def test_phase431_qss_and_tokens_present():
    from theme.brand import BRAND

    qss = _qss_source()
    for key in REQUIRED_TOKEN_KEYS:
        assert key in BRAND
    for marker in REQUIRED_QSS_MARKERS:
        assert marker in qss


def test_phase431_horizontal_layout_order():
    source = _login_source()
    positions = [source.find(token) for token in ORDER_TOKENS]
    assert all(pos >= 0 for pos in positions)
    assert positions == sorted(positions)


def test_phase431_guard_summary_ready():
    summary = horizontal_branded_login_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 40
