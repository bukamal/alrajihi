# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))

from workspace.quality.reports_workspace_visual_refactor_contract import phase449_reports_workspace_visual_refactor_summary


def test_phase449_reports_visual_refactor_ready():
    summary = phase449_reports_workspace_visual_refactor_summary(ROOT)
    assert summary["ready"], summary["details"]
    assert summary["issues"] == 0


def test_reports_qss_overrides_operational_and_legacy_rules():
    qss = (ROOT / "alrajhi_client/theme/qss.py").read_text(encoding="utf-8")
    assert "Phase449: reports workspace visual refactor" in qss
    assert qss.find("Phase449: reports workspace visual refactor") > qss.find("Phase448: Operational POS/Restaurant surface migration")
    assert 'QTabWidget[visualRole="reports_group_tabs"]' in qss
    assert 'QTableView[visualRole="reports_table"]' in qss


def test_reports_widget_uses_semantic_roles_not_local_styles():
    reports = (ROOT / "alrajhi_client/views/widgets/reports_widget.py").read_text(encoding="utf-8")
    assert "_apply_report_filter_roles" in reports
    assert "reports_filter_ribbon" in reports
    assert "reports_group_tabs" in reports
    assert "reports_inner_tabs" in reports
    assert "reports_table" in reports
    assert ".setStyleSheet" not in reports
