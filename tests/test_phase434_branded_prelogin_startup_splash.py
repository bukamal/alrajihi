# -*- coding: utf-8 -*-
"""Phase 434 branded pre-login startup splash tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.branded_prelogin_startup_splash_contract import (  # noqa: E402
    FORBIDDEN_SPLASH_MARKERS,
    MINIMUM_TOKEN_VALUES,
    REQUIRED_QSS_MARKERS,
    REQUIRED_SPLASH_MARKERS,
    REQUIRED_TOKEN_KEYS,
    branded_prelogin_startup_splash_summary,
)


def _splash_source() -> str:
    return (ROOT / "alrajhi_client" / "views" / "splash_screen.py").read_text(encoding="utf-8")


def _qss_source() -> str:
    return (ROOT / "alrajhi_client" / "theme" / "qss.py").read_text(encoding="utf-8")


def test_phase434_splash_markers_present():
    source = _splash_source()
    for marker in REQUIRED_SPLASH_MARKERS:
        assert marker in source


def test_phase434_legacy_splash_markers_removed():
    source = _splash_source()
    for marker in FORBIDDEN_SPLASH_MARKERS:
        assert marker not in source


def test_phase434_tokens_ready():
    from theme.brand import BRAND

    assert int(BRAND["brand_phase"]) >= 434
    for key in REQUIRED_TOKEN_KEYS:
        assert key in BRAND
    for key, minimum in MINIMUM_TOKEN_VALUES.items():
        assert int(BRAND[key]) >= minimum


def test_phase434_qss_markers_present():
    qss = _qss_source()
    for marker in REQUIRED_QSS_MARKERS:
        assert marker in qss


def test_phase434_guard_summary_ready():
    summary = branded_prelogin_startup_splash_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 40
