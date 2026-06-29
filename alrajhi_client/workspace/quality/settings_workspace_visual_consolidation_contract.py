# -*- coding: utf-8 -*-
"""Phase451 Settings Workspace Visual Consolidation contract.

Static/Qt-free guard: settings screens must use centralized dynamic-property
roles and theme/qss.py selectors instead of local page-level QSS overlays.
The phase is visual only and must not alter SettingsService persistence, save
handlers, tab registry keys, or grouped navigation membership.
"""
from __future__ import annotations
from pathlib import Path

REQUIRED_BRAND_TOKENS = [
    "settings_workspace_visual_phase",
    "settings_workspace_surface_bg",
    "settings_workspace_panel_bg",
    "settings_workspace_panel_border",
    "settings_workspace_card_bg",
    "settings_workspace_card_border",
    "settings_workspace_card_title_bg",
    "settings_workspace_group_tab_bg",
    "settings_workspace_group_tab_active_bg",
    "settings_workspace_leaf_tab_bg",
    "settings_workspace_leaf_tab_active_bg",
    "settings_workspace_input_bg",
    "settings_workspace_primary_bg",
    "settings_workspace_note_info_bg",
    "settings_workspace_table_header_bg",
]

REQUIRED_QSS_MARKERS = [
    "Phase451: settings workspace visual consolidation",
    'QWidget[settingsVisualPhase="451"]',
    'visualRole="settings_workspace"',
    'visualRole="settings_group_tabs"',
    'visualRole="settings_leaf_tabs"',
    'visualRole="settings_card"',
    'visualRole="settings_header"',
    'visualRole="settings_input"',
    'visualRole="settings_primary_action"',
    'visualRole="settings_action"',
    'visualRole="settings_note"',
    'visualRole="settings_table"',
]

REQUIRED_SETTINGS_WIDGET_MARKERS = [
    "settingsVisualPhase', 451",
    "visualWorkspaceType', 'settings'",
    "visualRole', 'settings_workspace'",
    "visualRole', 'settings_group_tabs'",
    "visualRole', 'settings_leaf_tabs'",
    "visualRole', 'settings_card'",
    "visualRole', 'settings_input'",
    "visualRole', 'settings_note'",
    "settingsLocalStylesSuppressed",
    "def _apply_settings_visual_template",
    "settings_workspace_visual_consolidation",
]

REQUIRED_RUNTIME_MARKERS = [
    "def _apply_settings_workspace_template",
    'root.setProperty("settingsVisualPhase", 451)',
    'root.setProperty("visualWorkspaceType", "settings")',
    '"settings_group_tabs"',
    '"settings_leaf_tabs"',
    '"settings_card"',
    '"settings_input"',
    '"settings_table"',
    '_apply_settings_workspace_template(root, policy)',
]

REQUIRED_DOCUMENT_SETTINGS_MARKERS = [
    "settingsVisualPhase', 451",
    "visualWorkspaceType', 'settings'",
    "visualRole', 'settings_document_surface'",
    "visualRole', 'settings_header'",
    "visualRole', 'settings_title'",
    "visualRole', 'settings_help'",
    "visualRole', 'settings_primary_action'",
    "settingsLocalStylesSuppressed",
]

FORBIDDEN_SETTINGS_WIDGET_SNIPPETS = [
    "self.setStyleSheet(self.styleSheet() + f\"\"\"",
    "Phase405: Basit settings surface overlay.",
    "QGroupBox#settingsCard[basitSettingsCard=\"true\"]::title",
    "apply_modern_widget(self)",
]

CRITICAL_SAVE_MARKERS = [
    "settings_service.set",
    "settings_service.clear_cache",
    "save_appearance_settings",
    "save_language_settings",
    "save_currency_settings",
    "backup_service",
]


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


def phase451_settings_workspace_visual_consolidation_summary(root: str | Path) -> dict:
    root = Path(root)
    details: list[str] = []
    checks = 0

    brand = _read(root, "alrajhi_client/theme/brand.py")
    for token in REQUIRED_BRAND_TOKENS:
        checks += 1
        if token not in brand:
            details.append(f"missing Phase451 settings brand token: {token}")
    checks += 1
    if "'settings_workspace_visual_phase': 451" not in brand:
        details.append("settings_workspace_visual_phase must be 451")
    checks += 1
    if "'project_visual_identity_phase': 451" not in brand:
        details.append("project_visual_identity_phase must advance to 451")

    qss = _read(root, "alrajhi_client/theme/qss.py")
    for marker in REQUIRED_QSS_MARKERS:
        checks += 1
        if marker not in qss:
            details.append(f"central QSS missing settings marker: {marker}")
    checks += 1
    if qss.find("Phase451: settings workspace visual consolidation") < qss.find("Phase450: unified document editor visual template"):
        details.append("Phase451 settings QSS must come after Phase450 document rules")

    settings_widget = _read(root, "alrajhi_client/views/widgets/settings_widget.py")
    for marker in REQUIRED_SETTINGS_WIDGET_MARKERS:
        checks += 1
        if marker not in settings_widget:
            details.append(f"settings widget missing visual marker: {marker}")
    for snippet in FORBIDDEN_SETTINGS_WIDGET_SNIPPETS:
        checks += 1
        if snippet in settings_widget:
            details.append(f"settings widget still contains legacy/local style snippet: {snippet}")
    for marker in CRITICAL_SAVE_MARKERS:
        checks += 1
        if marker not in settings_widget:
            details.append(f"settings widget lost critical non-visual marker: {marker}")

    runtime = _read(root, "alrajhi_client/ui/runtime_visual_polish.py")
    for marker in REQUIRED_RUNTIME_MARKERS:
        checks += 1
        if marker not in runtime:
            details.append(f"runtime visual polish missing settings marker: {marker}")

    doc_tabs = _read(root, "alrajhi_client/features/settings/settings_document_tabs.py")
    for marker in REQUIRED_DOCUMENT_SETTINGS_MARKERS:
        checks += 1
        if marker not in doc_tabs:
            details.append(f"settings document tabs missing visual marker: {marker}")
    for marker in ("workspace_save", "settings_service.set", "settings_service.clear_cache", "show_toast"):
        checks += 1
        if marker not in doc_tabs:
            details.append(f"settings document tabs lost persistence marker: {marker}")

    return {
        "ready": not details,
        "issues": len(details),
        "checks": checks,
        "details": details,
        "phase": 451,
    }


__all__ = ["phase451_settings_workspace_visual_consolidation_summary"]
