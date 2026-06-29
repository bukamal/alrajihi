# -*- coding: utf-8 -*-
"""Phase 437 dashboard visual identity alignment tests."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.dashboard_visual_identity_alignment_contract import (  # noqa: E402
    FORBIDDEN_DASHBOARD_SNIPPETS,
    REQUIRED_BRAND_TOKENS,
    REQUIRED_DASHBOARD_MARKERS,
    dashboard_visual_identity_summary,
)


def test_phase437_dashboard_widget_declares_identity_surface():
    source = (ROOT / "alrajhi_client" / "views" / "widgets" / "dashboard_widget.py").read_text(encoding="utf-8")
    for marker in REQUIRED_DASHBOARD_MARKERS:
        assert marker in source


def test_phase437_dashboard_no_old_hard_basit_panel_styles():
    source = (ROOT / "alrajhi_client" / "views" / "widgets" / "dashboard_widget.py").read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_DASHBOARD_SNIPPETS:
        assert forbidden not in source


def test_phase437_brand_tokens_are_centralized():
    source = (ROOT / "alrajhi_client" / "theme" / "brand.py").read_text(encoding="utf-8")
    for marker in REQUIRED_BRAND_TOKENS:
        assert marker in source


def test_phase437_contract_summary_ready():
    summary = dashboard_visual_identity_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0
    assert summary["checks"] >= 30
