# -*- coding: utf-8 -*-
"""Phase 368 login password visibility button alignment tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.login_password_toggle_alignment_contract import (  # noqa: E402
    FORBIDDEN_OVERLAY_MARKERS,
    ORDER_TOKENS,
    PHASE368_MARKER,
    REQUIRED_ALIGNMENT_MARKERS,
    REQUIRED_QSS_MARKERS,
    login_password_toggle_alignment_summary,
)


def _login_source() -> str:
    return (ROOT / "alrajhi_client" / "views" / "dialogs" / "login_dialog.py").read_text(encoding="utf-8")


def _qss_source() -> str:
    return (ROOT / "alrajhi_client" / "theme" / "qss.py").read_text(encoding="utf-8")


def test_phase368_login_password_toggle_markers_present():
    source = _login_source()
    assert PHASE368_MARKER in source
    for marker in REQUIRED_ALIGNMENT_MARKERS:
        assert marker in source


def test_phase368_login_password_toggle_qss_geometry_present():
    source = _qss_source()
    for marker in REQUIRED_QSS_MARKERS:
        assert marker in source


def test_phase368_login_password_toggle_not_overlay_based():
    source = _login_source()
    for marker in FORBIDDEN_OVERLAY_MARKERS:
        assert marker not in source


def test_phase368_password_layout_order_is_safe():
    source = _login_source()
    positions = [source.find(token) for token in ORDER_TOKENS]
    assert all(pos >= 0 for pos in positions)
    assert positions == sorted(positions)


def test_phase368_guard_summary_ready():
    summary = login_password_toggle_alignment_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 25
