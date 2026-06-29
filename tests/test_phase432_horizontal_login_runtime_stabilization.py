# -*- coding: utf-8 -*-
"""Phase 432 horizontal login runtime stabilization tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.horizontal_login_runtime_stabilization_contract import (  # noqa: E402
    FORBIDDEN_RUNTIME_MARKERS,
    MINIMUM_TOKEN_VALUES,
    REQUIRED_LOGIN_MARKERS,
    REQUIRED_QSS_MARKERS,
    REQUIRED_TOKEN_KEYS,
    horizontal_login_runtime_stabilization_summary,
)


def _login_source() -> str:
    return (ROOT / "alrajhi_client" / "views" / "dialogs" / "login_dialog.py").read_text(encoding="utf-8")


def _qss_source() -> str:
    return (ROOT / "alrajhi_client" / "theme" / "qss.py").read_text(encoding="utf-8")


def test_phase432_runtime_markers_present():
    source = _login_source()
    for marker in REQUIRED_LOGIN_MARKERS:
        assert marker in source


def test_phase432_unstable_markers_removed():
    source = _login_source()
    for marker in FORBIDDEN_RUNTIME_MARKERS:
        assert marker not in source


def test_phase432_tokens_and_values_ready():
    from theme.brand import BRAND

    for key in REQUIRED_TOKEN_KEYS:
        assert key in BRAND
    for key, minimum in MINIMUM_TOKEN_VALUES.items():
        assert int(BRAND.get(key, 0)) >= minimum


def test_phase432_qss_markers_present():
    qss = _qss_source()
    for marker in REQUIRED_QSS_MARKERS:
        assert marker in qss


def test_phase432_runtime_guard_summary_ready():
    summary = horizontal_login_runtime_stabilization_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 45
