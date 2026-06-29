# -*- coding: utf-8 -*-
"""Phase 438 main shell responsive runtime fit tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.main_shell_responsive_runtime_fit_contract import (  # noqa: E402
    REQUIRED_DASHBOARD_RESPONSIVE_MARKERS,
    REQUIRED_MAIN_ENTRY_MARKERS,
    REQUIRED_MAIN_WINDOW_MARKERS,
    REQUIRED_RUNTIME_FIT_MODULE_MARKERS,
    main_shell_responsive_runtime_fit_summary,
)


def test_phase438_runtime_fit_module_declares_policy():
    source = (ROOT / "alrajhi_client" / "ui" / "main_shell_runtime_fit.py").read_text(encoding="utf-8")
    for marker in REQUIRED_RUNTIME_FIT_MODULE_MARKERS:
        assert marker in source


def test_phase438_main_window_uses_screen_aware_sizing():
    source = (ROOT / "alrajhi_client" / "views" / "main_window.py").read_text(encoding="utf-8")
    for marker in REQUIRED_MAIN_WINDOW_MARKERS:
        assert marker in source
    assert "self.setMinimumSize(1200, 700)" not in source
    assert "self.resize(1400, 900)" not in source


def test_phase438_main_entry_shows_window_through_runtime_fit_helper():
    source = (ROOT / "alrajhi_client" / "main.py").read_text(encoding="utf-8")
    for marker in REQUIRED_MAIN_ENTRY_MARKERS:
        assert marker in source
    assert "\n    window.show()\n    timeline.mark(\"main_window_shown\"" not in source


def test_phase438_dashboard_declares_responsive_runtime_surface():
    dashboard = (ROOT / "alrajhi_client" / "views" / "widgets" / "dashboard_widget.py").read_text(encoding="utf-8")
    brand = (ROOT / "alrajhi_client" / "theme" / "brand.py").read_text(encoding="utf-8")
    for marker in REQUIRED_DASHBOARD_RESPONSIVE_MARKERS:
        source = dashboard if marker != "dashboard_responsive_phase" else brand
        assert marker in source


def test_phase438_contract_summary_ready():
    summary = main_shell_responsive_runtime_fit_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 15
