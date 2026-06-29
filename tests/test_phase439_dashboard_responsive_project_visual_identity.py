# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.dashboard_responsive_project_visual_identity_contract import (
    REQUIRED_DASHBOARD_MARKERS,
    REQUIRED_VISUAL_IDENTITY_MARKERS,
    FORBIDDEN_DASHBOARD_PATTERNS,
    dashboard_responsive_project_visual_identity_summary,
)


def test_phase439_dashboard_uses_responsive_grid_not_fixed_hbox():
    source = (ROOT / "alrajhi_client" / "views" / "widgets" / "dashboard_widget.py").read_text(encoding="utf-8")
    for marker in REQUIRED_DASHBOARD_MARKERS:
        assert marker in source or marker in (ROOT / "alrajhi_client" / "theme" / "brand.py").read_text(encoding="utf-8")
    for pattern in FORBIDDEN_DASHBOARD_PATTERNS:
        assert pattern not in source


def test_phase439_project_visual_identity_is_applied_to_tabs_and_lazy_pages():
    combined = "\n".join([
        (ROOT / "alrajhi_client" / "theme" / "brand.py").read_text(encoding="utf-8"),
        (ROOT / "alrajhi_client" / "theme" / "qss.py").read_text(encoding="utf-8"),
        (ROOT / "alrajhi_client" / "ui" / "runtime_visual_polish.py").read_text(encoding="utf-8"),
        (ROOT / "alrajhi_client" / "views" / "main_window.py").read_text(encoding="utf-8"),
    ])
    for marker in REQUIRED_VISUAL_IDENTITY_MARKERS:
        assert marker in combined


def test_phase439_contract_summary_ready():
    summary = dashboard_responsive_project_visual_identity_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 20
