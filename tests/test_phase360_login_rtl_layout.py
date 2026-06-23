# -*- coding: utf-8 -*-
"""Phase 360 login compatibility test.

Phase367 intentionally restores the LoginDialog visual design to the original
pre-Phase350 baseline. Earlier experimental login layout contracts are treated
as superseded when the Phase367 marker is present.
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


def test_phase367_pre350_original_login_restore_marker():
    source = (ROOT / "alrajhi_client" / "views" / "dialogs" / "login_dialog.py").read_text(encoding="utf-8")
    assert "Phase367: restored LoginDialog visual structure to the pre-Phase350 original baseline." in source
    assert "layout = QVBoxLayout(self.content_widget)" in source
    assert "pwd_layout = QHBoxLayout()" in source
    assert "options_layout = QHBoxLayout()" in source
    assert "brand_side_panel(" not in source
    assert "loginPasswordSafeSpacer" not in source
    assert "logo.setObjectName('brandMark')" not in source
