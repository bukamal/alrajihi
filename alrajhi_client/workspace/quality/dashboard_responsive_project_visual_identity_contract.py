# -*- coding: utf-8 -*-
"""Phase 439 contract for dashboard responsiveness and project-wide visual identity."""
from __future__ import annotations
from pathlib import Path

REQUIRED_DASHBOARD_MARKERS = (
    "DashboardResponsiveGridHost",
    "_dashboard_responsive_column_count",
    "_apply_dashboard_responsive_layout",
    "dashboard_one_column_breakpoint",
    "dashboard_two_column_breakpoint",
    "dashboardResponsiveColumns",
    "quick_actions_grid",
    "quick_action_buttons",
    "resizeEvent",
)

REQUIRED_VISUAL_IDENTITY_MARKERS = (
    "project_visual_identity_phase",
    "projectVisualIdentityPhase",
    "workspace_surface",
    "workspace_card",
    "workspace_tabs",
    "QTabWidget[projectVisualIdentityPhase=\"439\"]",
    "apply_runtime_visual_polish(page, page_key)",
    "apply_runtime_visual_polish(dashboard, 'dashboard')",
)

FORBIDDEN_DASHBOARD_PATTERNS = (
    "row = QHBoxLayout()\n        row.setDirection(QBoxLayout.RightToLeft)",
    "row.addWidget(self.quick_panel, 5)",
    "row.addWidget(self.company_panel, 4)",
    "row.addWidget(self.project_panel, 5)",
)


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def dashboard_responsive_project_visual_identity_summary(root: Path) -> dict:
    dashboard = _read(root, "alrajhi_client/views/widgets/dashboard_widget.py")
    brand = _read(root, "alrajhi_client/theme/brand.py")
    qss = _read(root, "alrajhi_client/theme/qss.py")
    polish = _read(root, "alrajhi_client/ui/runtime_visual_polish.py")
    main_window = _read(root, "alrajhi_client/views/main_window.py")
    combined = "\n".join([dashboard, brand, qss, polish, main_window])
    issues = []
    for marker in REQUIRED_DASHBOARD_MARKERS:
        if marker not in combined:
            issues.append(f"missing dashboard marker: {marker}")
    for marker in REQUIRED_VISUAL_IDENTITY_MARKERS:
        if marker not in combined:
            issues.append(f"missing visual identity marker: {marker}")
    for pattern in FORBIDDEN_DASHBOARD_PATTERNS:
        if pattern in dashboard:
            issues.append(f"forbidden fixed dashboard pattern: {pattern[:48]}")
    return {"ready": not issues, "issues": len(issues), "details": issues, "checks": len(REQUIRED_DASHBOARD_MARKERS) + len(REQUIRED_VISUAL_IDENTITY_MARKERS) + len(FORBIDDEN_DASHBOARD_PATTERNS)}
