# -*- coding: utf-8 -*-
"""Phase 437 dashboard visual identity alignment contract.

The dashboard must follow the project identity used by the branded startup,
login, and operational surfaces. This contract is intentionally Qt-free so it
can run in CI without a GUI runtime.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

REQUIRED_DASHBOARD_MARKERS = (
    "dashboardVisualPhase",
    "identity_aligned",
    "dashboardPanelRole",
    "dashboardActionTier",
    "dashboard_shortcut_primary_bg",
    "dashboard_shortcut_secondary_bg",
    "dashboard_shortcut_finance_bg",
    "CompanyLogoBox { background: #ffffff; border: 1px solid #D8E5F2; border-radius: 16px",
    "CashBalanceBox { background: #FFF7ED; border: 1px solid #FED7AA; border-radius: 16px",
    "DeveloperBrandPanel",
)

REQUIRED_LEGACY_COMPONENT_MARKERS = (
    "Phase437: shortcuts now follow the product identity system",
    "dashboardVisualPhase",
    "dashboard_panel_radius",
    "dashboard_panel_header_bg",
    "basitCard",  # kept only as compatibility property, set to False for dashboard shortcuts
)

REQUIRED_BRAND_TOKENS = (
    "dashboard_visual_phase",
    "dashboard_panel_radius",
    "dashboard_panel_min_height",
    "dashboard_panel_bg",
    "dashboard_panel_header_bg",
    "dashboard_shortcut_height",
    "dashboard_shortcut_radius",
    "dashboard_shortcut_primary_bg",
    "dashboard_shortcut_secondary_bg",
    "dashboard_shortcut_finance_bg",
    "dashboard_cash_balance_bg",
)

FORBIDDEN_DASHBOARD_SNIPPETS = (
    "QFrame#DashboardQuickActionsPanel { background: #edf2f7; border: 1px solid #aab8cc; border-radius: 2px; }",
    "QFrame#DashboardCompanyPanel { background: #edf2f7; border: 1px solid #aab8cc; border-radius: 2px; }",
    "QFrame#DashboardCashPanel { background: #edf2f7; border: 1px solid #aab8cc; border-radius: 2px; }",
    "QLabel#CashSectionTitle { background: #f5c542; color: #1f2937; border: 1px solid #aab8cc; border-radius: 2px;",
)


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def dashboard_visual_identity_matrix(root: Path) -> List[Dict[str, str]]:
    dashboard = _read(root, "alrajhi_client/views/widgets/dashboard_widget.py")
    legacy = _read(root, "alrajhi_client/views/widgets/dashboard_legacy_components.py")
    brand = _read(root, "alrajhi_client/theme/brand.py")
    rows: List[Dict[str, str]] = []
    for marker in REQUIRED_DASHBOARD_MARKERS:
        rows.append({"area": "dashboard_widget", "check": marker, "status": "pass" if marker in dashboard else "fail"})
    for marker in REQUIRED_LEGACY_COMPONENT_MARKERS:
        rows.append({"area": "dashboard_components", "check": marker, "status": "pass" if marker in legacy else "fail"})
    for marker in REQUIRED_BRAND_TOKENS:
        rows.append({"area": "brand_tokens", "check": marker, "status": "pass" if marker in brand else "fail"})
    for marker in FORBIDDEN_DASHBOARD_SNIPPETS:
        rows.append({"area": "legacy_dashboard_visuals", "check": marker, "status": "fail" if marker in dashboard else "pass"})
    return rows


def dashboard_visual_identity_summary(root: Path) -> Dict[str, object]:
    rows = dashboard_visual_identity_matrix(root)
    issues = [row for row in rows if row["status"] != "pass"]
    return {
        "phase": 437,
        "ready": not issues,
        "checks": len(rows),
        "issues": len(issues),
        "identity": "login_splash_dashboard_aligned",
    }
