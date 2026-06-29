# -*- coding: utf-8 -*-
"""Phase447 unified list workspace visual template contract.

This contract is intentionally static/Qt-free. It verifies that recurring list
surfaces (invoices, returns, parties, users, vouchers and generic BaseWidget
screens) use a single semantic visual template rather than each screen keeping
its own heavy toolbar/table style.
"""
from __future__ import annotations
from pathlib import Path

REQUIRED_BRAND_TOKENS = [
    "list_workspace_visual_phase",
    "list_workspace_filter_bg",
    "list_workspace_filter_border",
    "list_workspace_action_bg",
    "list_workspace_primary_bg",
    "list_workspace_danger_bg",
    "list_workspace_counter_bg",
    "list_workspace_table_header_bg",
]

REQUIRED_QSS_MARKERS = [
    "Phase447: unified list workspace visual template",
    'QWidget[listWorkspaceVisualTemplatePhase="447"]',
    'visualRole="list_filter_bar"',
    'visualRole="list_search_input"',
    'visualRole="list_primary_action"',
    'visualRole="list_danger_action"',
    'visualRole="list_counter"',
    'visualRole="list_table"',
]

REQUIRED_TOOLBAR_MARKERS = [
    "listWorkspaceVisualTemplatePhase", 
    "unified_list_workspace_template",
    "list_filter_bar",
    "list_primary_action",
    "list_danger_action",
    "list_search_input",
    "list_counter",
]

REQUIRED_RUNTIME_MARKERS = [
    "_apply_list_workspace_template",
    "Phase447: normalize list/grid screens",
    "list_workspace_surface",
    "list_filter_input",
    "list_table",
    "list_counter",
]

REQUIRED_BASE_WIDGET_MARKERS = [
    "listWorkspaceVisualTemplatePhase",
    "list_workspace_surface",
    "list_filter_bar",
    "visualRole', 'list_table'",
]

FORBIDDEN_PHASE447_REGRESSIONS = []


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def phase447_unified_list_workspace_visual_template_summary(root: str | Path) -> dict:
    root = Path(root)
    details: list[str] = []
    checks = 0

    brand = _read(root, "alrajhi_client/theme/brand.py")
    for token in REQUIRED_BRAND_TOKENS:
        checks += 1
        if token not in brand:
            details.append(f"missing Phase447 brand token: {token}")
    checks += 1
    if not any(marker in brand for marker in ("'project_visual_identity_phase': 447", "'project_visual_identity_phase': 448", "'project_visual_identity_phase': 449", "'project_visual_identity_phase': 450", "'project_visual_identity_phase': 451")):
        details.append("project_visual_identity_phase must be advanced to 447")
    checks += 1
    if not any(marker in brand for marker in ("'legacy_visual_style_sweep_phase': 447", "'legacy_visual_style_sweep_phase': 448", "'legacy_visual_style_sweep_phase': 449", "'legacy_visual_style_sweep_phase': 450", "'legacy_visual_style_sweep_phase': 451")):
        details.append("legacy_visual_style_sweep_phase must be advanced to 447")
    for marker in FORBIDDEN_PHASE447_REGRESSIONS:
        checks += 1
        if marker in brand:
            details.append(f"brand still contains previous active phase marker: {marker}")

    qss = _read(root, "alrajhi_client/theme/qss.py")
    for marker in REQUIRED_QSS_MARKERS:
        checks += 1
        if marker not in qss:
            details.append(f"central QSS missing list-template marker: {marker}")
    checks += 1
    if qss.find("Phase447: unified list workspace visual template") < qss.find("Phase404: Basit-inspired management/list workspaces"):
        details.append("Phase447 list template must be declared after Phase404 Basit list styles so it overrides legacy chrome")

    toolbar = _read(root, "alrajhi_client/views/widgets/components/table_toolbar.py")
    for marker in REQUIRED_TOOLBAR_MARKERS:
        checks += 1
        if marker not in toolbar:
            details.append(f"TableToolbar missing list-template marker: {marker}")

    runtime = _read(root, "alrajhi_client/ui/runtime_visual_polish.py")
    for marker in REQUIRED_RUNTIME_MARKERS:
        checks += 1
        if marker not in runtime:
            details.append(f"runtime visual polish missing list-template marker: {marker}")

    base = _read(root, "alrajhi_client/views/widgets/base_widget.py")
    for marker in REQUIRED_BASE_WIDGET_MARKERS:
        checks += 1
        if marker not in base:
            details.append(f"BaseWidget missing list-template marker: {marker}")

    list_contract = _read(root, "alrajhi_client/workspace/lists/list_workspace_contract.py")
    for list_key in ("sales_invoices", "purchase_invoices", "customers", "suppliers"):
        checks += 1
        if list_key not in list_contract:
            details.append(f"list workspace descriptor not covered: {list_key}")

    return {
        "ready": not details,
        "issues": len(details),
        "checks": checks,
        "details": details,
        "phase": 447,
    }


__all__ = ["phase447_unified_list_workspace_visual_template_summary"]
