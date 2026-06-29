# -*- coding: utf-8 -*-
"""Phase 435 login-to-main transition tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.login_to_main_transition_contract import (  # noqa: E402
    REQUIRED_MAIN_MARKERS,
    REQUIRED_OVERLAY_MARKERS,
    REQUIRED_PROFILER_MARKERS,
    login_to_main_transition_summary,
)
from workspace.runtime.startup_timeline_profiler import StartupTimelineProfiler  # noqa: E402


def test_phase435_main_runtime_wiring_present():
    main = (ROOT / "alrajhi_client" / "main.py").read_text(encoding="utf-8")
    for marker in REQUIRED_MAIN_MARKERS:
        assert marker in main


def test_phase435_overlay_contract_present():
    overlay = (ROOT / "alrajhi_client" / "ui" / "post_login_transition_overlay.py").read_text(encoding="utf-8")
    for marker in REQUIRED_OVERLAY_MARKERS:
        assert marker in overlay


def test_phase435_profiler_contract_present():
    source = (ROOT / "alrajhi_client" / "workspace" / "runtime" / "startup_timeline_profiler.py").read_text(encoding="utf-8")
    for marker in REQUIRED_PROFILER_MARKERS:
        assert marker in source


def test_phase435_profiler_summary_and_export(tmp_path):
    profiler = StartupTimelineProfiler()
    profiler.mark("login_accepted", category="login")
    profiler.mark("main_window_shown", category="post_login")
    exported = profiler.export(tmp_path)
    assert exported["json"].exists()
    assert exported["csv"].exists()
    summary = profiler.summary()
    assert summary["marker"] == "phase435_login_to_mainwindow_transition_profiler"
    assert summary["post_login_to_main_ms"] is not None


def test_phase435_guard_summary_ready():
    summary = login_to_main_transition_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 35
