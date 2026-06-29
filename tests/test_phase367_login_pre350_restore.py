# -*- coding: utf-8 -*-
"""Phase 367 login pre-Phase350 original design restore tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.login_pre350_restore_contract import (  # noqa: E402
    FORBIDDEN_REDESIGN_MARKERS,
    ORDER_TOKENS,
    PHASE367_MARKER,
    REQUIRED_PRE350_MARKERS,
    login_pre350_restore_summary,
)


def _login_source() -> str:
    return (ROOT / "alrajhi_client" / "views" / "dialogs" / "login_dialog.py").read_text(encoding="utf-8")


def test_phase367_login_original_markers_present():
    source = _login_source()
    assert PHASE367_MARKER in source
    for marker in REQUIRED_PRE350_MARKERS:
        assert marker in source


def test_phase367_login_post350_redesign_markers_absent():
    source = _login_source()
    for marker in FORBIDDEN_REDESIGN_MARKERS:
        assert marker not in source


def test_phase367_login_original_order_is_restored():
    source = _login_source()
    positions = [source.find(token) for token in ORDER_TOKENS]
    assert all(pos >= 0 for pos in positions)
    assert positions == sorted(positions)


def test_phase367_guard_summary_ready():
    summary = login_pre350_restore_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 30
