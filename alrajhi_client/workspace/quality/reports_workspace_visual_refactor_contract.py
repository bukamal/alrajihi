# -*- coding: utf-8 -*-
"""Phase449 Reports Workspace Visual Refactor contract.

Static/Qt-free guard: reports must use a dedicated visual template for the
filter ribbon, report family tabs, result tables, and summary bar.  This avoids
regressing to the older stacked-toolbar report surface while preserving report
calculation/data paths.
"""
from __future__ import annotations
from pathlib import Path

REQUIRED_BRAND_TOKENS = [
    "reports_workspace_visual_phase",
    "reports_filter_ribbon_bg",
    "reports_filter_input_bg",
    "reports_group_tab_bg",
    "reports_group_tab_active_bg",
    "reports_inner_tab_bg",
    "reports_table_header_bg",
    "reports_summary_bg",
    "reports_primary_bg",
]

REQUIRED_QSS_MARKERS = [
    "Phase449: reports workspace visual refactor",
    'QWidget[reportsVisualPhase="449"]',
    'visualRole="reports_workspace"',
    'visualRole="reports_filter_ribbon"',
    'visualRole="reports_filter_input"',
    'visualRole="reports_primary_action"',
    'visualRole="reports_secondary_action"',
    'visualRole="reports_group_tabs"',
    'visualRole="reports_inner_tabs"',
    'visualRole="reports_table"',
    'visualRole="reports_summary_bar"',
]

REQUIRED_REPORTS_WIDGET_MARKERS = [
    "self.setProperty('reportsVisualPhase', 449)",
    "self.setProperty('visualRole', 'reports_workspace')",
    "period_frame.setProperty('visualRole', 'reports_filter_ribbon')",
    "self._apply_report_filter_roles(reset_btn)",
    "widget.setProperty('visualRole', 'reports_filter_input')",
    "self.refresh_btn.setProperty('visualRole', 'reports_primary_action')",
    "reset_btn.setProperty('visualRole', 'reports_secondary_action')",
    "self.tabs.setProperty('visualRole', 'reports_group_tabs')",
    "group_tabs.setProperty('visualRole', 'reports_inner_tabs')",
    "self.report_summary.setProperty('visualRole', 'reports_summary_bar')",
    "table.setProperty('visualRole', 'reports_table')",
]

FORBIDDEN_REPORTS_REGRESSIONS = [
    "self.period_type.setStyleSheet",
    "self.refresh_btn.setStyleSheet",
    "self.report_summary.setStyleSheet",
]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def phase449_reports_workspace_visual_refactor_summary(root: str | Path) -> dict:
    root = Path(root)
    details: list[str] = []
    checks = 0

    brand = _read(root, "alrajhi_client/theme/brand.py")
    for token in REQUIRED_BRAND_TOKENS:
        checks += 1
        if token not in brand:
            details.append(f"missing Phase449 report brand token: {token}")
    checks += 1
    if "'reports_workspace_visual_phase': 449" not in brand:
        details.append("reports_workspace_visual_phase must be 449")

    qss = _read(root, "alrajhi_client/theme/qss.py")
    for marker in REQUIRED_QSS_MARKERS:
        checks += 1
        if marker not in qss:
            details.append(f"central QSS missing reports marker: {marker}")
    checks += 1
    if qss.find("Phase449: reports workspace visual refactor") < qss.find("Phase448: Operational POS/Restaurant surface migration"):
        details.append("Phase449 reports QSS must come after Phase448 operational rules")

    reports = _read(root, "alrajhi_client/views/widgets/reports_widget.py")
    for marker in REQUIRED_REPORTS_WIDGET_MARKERS:
        checks += 1
        if marker not in reports:
            details.append(f"ReportsWidget missing Phase449 marker: {marker}")
    for marker in FORBIDDEN_REPORTS_REGRESSIONS:
        checks += 1
        if marker in reports:
            details.append(f"ReportsWidget still has direct local styling: {marker}")

    return {
        "ready": not details,
        "issues": len(details),
        "checks": checks,
        "details": details,
        "phase": 449,
    }


__all__ = ["phase449_reports_workspace_visual_refactor_summary"]
