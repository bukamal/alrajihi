# -*- coding: utf-8 -*-
"""Phase 360 login compatibility test.

Phase431 intentionally replaces the narrow vertical LoginDialog with a horizontal branded split surface. Earlier login layout contracts are treated as superseded by the Phase431 marker.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def test_login_contract_is_clean_or_superseded_by_phase367():
    from workspace.quality.login_rtl_layout_contract import login_rtl_layout_summary

    summary = login_rtl_layout_summary(ROOT)
    assert summary["ready"] is True
    assert summary["issues"] == 0


def test_phase431_horizontal_branded_login_marker():
    source = (ROOT / "alrajhi_client" / "views" / "dialogs" / "login_dialog.py").read_text(encoding="utf-8")
    assert "Phase431: horizontal branded login layout" in source
    assert "root_layout = QHBoxLayout(self.content_widget)" in source
    assert "brand_side_panel(" in source
    assert "self.form_panel = first_run_form_panel()" in source
    assert "self.main_frame.setProperty('loginLayout', 'horizontal_branded_split')" in source
    assert "layout = QVBoxLayout(self.content_widget)" not in source
