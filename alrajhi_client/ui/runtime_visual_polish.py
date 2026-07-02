# -*- coding: utf-8 -*-
"""Runtime visual polish helpers for legacy and modern workspaces.

This module is deliberately defensive.  It applies safe properties and sizing
hints without touching business logic, services, printing, or data models.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QDateEdit,
    QHeaderView,
    QLabel,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QLineEdit,
    QPlainTextEdit,
    QSizePolicy,
    QSpinBox,
    QDoubleSpinBox,
    QTableView,
    QTableWidget,
    QTabWidget,
    QStyledItemDelegate,
    QTextEdit,
    QWidget,
)

from theme.brand import BRAND
from workspace.runtime.visual_polish_contract import workspace_visual_policy
from ui.table_direction_policy import apply_table_direction, apply_table_direction_tree
from ui.windows_runtime_visual_acceptance import apply_windows_runtime_visual_acceptance
from ui.runtime_layout_reconstruction import apply_runtime_layout_reconstruction
from ui.targeted_screen_rebuild import apply_targeted_screen_rebuild
from ui.single_screen_runtime_hardening import apply_single_screen_runtime_hardening
from ui.runtime_visual_regression_gate import apply_runtime_visual_regression_gate


_TABLE_ROW_SIZES = {"compact": 30, "comfortable": 36, "touch": 46}


class RuntimeCenterAlignDelegate(QStyledItemDelegate):
    """Display delegate that centers table cells project-wide.

    Kept local to runtime polish so it can be safely applied to legacy tables
    without touching business models or column-specific editors.
    """

    def paint(self, painter, option, index):  # type: ignore[override]
        option.displayAlignment = Qt.AlignCenter
        super().paint(painter, option, index)


def _set_if_empty_object_name(widget: QWidget, name: str) -> None:
    try:
        if not widget.objectName():
            widget.setObjectName(name)
    except Exception:
        pass


def _layout_apply(widget: QWidget, margin: int, spacing: int) -> None:
    layout = widget.layout()
    if layout is None:
        return
    try:
        # Keep shell-level zero margins intact.  Old content screens with nonzero
        # margins are normalized to tokenized values.
        current = layout.contentsMargins()
        if any((current.left(), current.top(), current.right(), current.bottom())):
            layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
    except Exception:
        pass


def _apply_table_polish(table: QTableView, density: str) -> None:
    apply_table_direction(table)
    if not table.property("visualRole"):
        table.setProperty("visualRole", "runtime_table")
    table.setAlternatingRowColors(True)
    table.setWordWrap(False)
    try:
        # Phase384: all display and editable-grid table cells are centered by
        # default.  Column-specific delegates remain effective where installed.
        table.setItemDelegate(RuntimeCenterAlignDelegate(table))
    except Exception:
        pass
    try:
        if isinstance(table, QTableWidget):
            for row in range(table.rowCount()):
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    if item is not None:
                        item.setTextAlignment(Qt.AlignCenter)
    except Exception:
        pass
    try:
        if bool(table.property("standard_table_keyboard")):
            table.setSelectionBehavior(QAbstractItemView.SelectItems)
        else:
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.ExtendedSelection)
    except Exception:
        pass
    try:
        if hasattr(table, "set_density"):
            table.set_density(density)
        else:
            table.verticalHeader().setDefaultSectionSize(_TABLE_ROW_SIZES.get(density, 36))
        table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        header = table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setSectionsClickable(True)
        header.setSectionsMovable(True)
        header.setMinimumSectionSize(72)
        if not header.stretchLastSection():
            header.setStretchLastSection(False)
    except Exception:
        pass


def _apply_input_polish(widget: QWidget) -> None:
    min_height = int(BRAND.get("input_min_height", 34))
    try:
        if widget.minimumHeight() < min_height:
            widget.setMinimumHeight(min_height)
    except Exception:
        pass


def _apply_button_polish(button: QAbstractButton, role: str) -> None:
    try:
        button.setProperty("visualRole", role)
        min_height = int(BRAND.get("action_button_min_height", 38))
        if button.minimumHeight() < min_height:
            button.setMinimumHeight(min_height)
        if button.sizePolicy().horizontalPolicy() == QSizePolicy.Fixed and button.minimumWidth() < 74:
            button.setMinimumWidth(74)
    except Exception:
        pass


def _list_action_role(button: QAbstractButton) -> str:
    name = (button.objectName() or "").lower()
    text = (button.text() or "").lower()
    if name in {"primary", "add", "new"} or "اضاف" in text or "جديد" in text or "add" in text or "new" in text:
        return "list_primary_action"
    if name == "danger" or "حذف" in text or "delete" in text:
        return "list_danger_action"
    if "filter" in text or "فلتر" in text or "بحث" in text:
        return "list_filter_action"
    return "list_action"


def _apply_list_workspace_template(root: QWidget, policy) -> None:
    """Phase447: normalize list/grid screens without touching their models."""
    if policy.workspace_type != "list" and not getattr(root, "list_workspace_descriptor", None):
        return
    try:
        root.setProperty("listWorkspaceVisualTemplatePhase", 447)
        root.setProperty("visualRole", "list_workspace_surface")
        root.setProperty("visualStyleSource", "unified_list_workspace_template")
    except Exception:
        pass
    for child in list(root.findChildren(QWidget)) if hasattr(root, "findChildren") else []:
        try:
            child.setProperty("listWorkspaceVisualTemplatePhase", 447)
            cname = child.__class__.__name__
            if bool(child.property("basitListToolbar")) or cname == "TableToolbar":
                child.setProperty("visualRole", "list_filter_bar")
                child.setProperty("visualStyleSource", "unified_list_workspace_template")
            elif isinstance(child, (QLineEdit, QComboBox, QDateEdit)):
                if not child.property("visualRole") or str(child.property("visualRole")).startswith("workspace"):
                    child.setProperty("visualRole", "list_filter_input")
                _apply_input_polish(child)
            elif isinstance(child, QAbstractButton):
                child.setProperty("visualRole", _list_action_role(child))
                _apply_button_polish(child, str(child.property("visualRole") or "list_action"))
            elif isinstance(child, QTableView):
                if child.property("visualRole") in (None, "", "runtime_table", "workspace_card"):
                    child.setProperty("visualRole", "list_table")
                child.setProperty("listWorkspaceVisualTemplatePhase", 447)
            elif isinstance(child, QLabel) and (bool(child.property("basitCounter")) or (child.objectName() or "").lower() in {"muted", "mutedlabel"}):
                child.setProperty("visualRole", "list_counter")
            elif isinstance(child, (QFrame, QGroupBox)) and (child.property("visualRole") in (None, "", "workspace_card", "card")):
                child.setProperty("visualRole", "list_card")
        except Exception:
            continue



def _settings_action_role(button: QAbstractButton) -> str:
    name = (button.objectName() or "").lower()
    text = (button.text() or "").lower()
    if name == "primary" or "حفظ" in text or "تطبيق" in text or "save" in text or "apply" in text:
        return "settings_primary_action"
    if name == "danger" or "حذف" in text or "delete" in text or "مسح" in text:
        return "settings_danger_action"
    return "settings_action"


def _apply_settings_workspace_template(root: QWidget, policy) -> None:
    """Phase451: normalize the settings workspace without touching values/save handlers."""
    page_id = str(getattr(policy, "page_id", "") or "")
    is_settings = page_id == "settings" or root.objectName() == "settingsWidget" or bool(root.property("basitSettingsSurface"))
    if not is_settings and getattr(policy, "workspace_type", "") != "settings":
        return
    try:
        root.setProperty("settingsVisualPhase", 451)
        root.setProperty("visualWorkspaceType", "settings")
        root.setProperty("visualRole", "settings_workspace")
        root.setProperty("visualStyleSource", "settings_workspace_visual_consolidation")
    except Exception:
        pass
    for child in list(root.findChildren(QWidget)) if hasattr(root, "findChildren") else []:
        try:
            child.setProperty("settingsVisualPhase", 451)
            child.setProperty("visualWorkspaceType", "settings")
            if isinstance(child, QTabWidget):
                if child.objectName() == "settingsTabs":
                    child.setProperty("visualRole", "settings_group_tabs")
                elif str(child.objectName()).startswith("settingsGroupTabs_") or bool(child.property("basitSettingsGroupTabs")):
                    child.setProperty("visualRole", "settings_leaf_tabs")
                else:
                    child.setProperty("visualRole", "settings_leaf_tabs")
                child.setDocumentMode(True)
            elif isinstance(child, (QFrame, QGroupBox)):
                if child.objectName() == "settingsCard" or child.property("basitSettingsCard"):
                    child.setProperty("visualRole", "settings_card")
                elif child.objectName() in {"DocumentHeaderCard", "settingsHeader"}:
                    child.setProperty("visualRole", "settings_header")
            elif isinstance(child, QLabel):
                if str(child.objectName()).startswith("note_") or child.property("basitSettingsNote"):
                    child.setProperty("visualRole", "settings_note")
                elif child.objectName() in {"settingsHelp", "DocumentHint"}:
                    child.setProperty("visualRole", "settings_help")
                elif child.objectName() in {"DocumentTitle", "settingsTitle"}:
                    child.setProperty("visualRole", "settings_title")
            elif isinstance(child, (QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox)):
                child.setProperty("visualRole", "settings_input")
                _apply_input_polish(child)
            elif isinstance(child, QAbstractButton):
                role = _settings_action_role(child)
                child.setProperty("visualRole", role)
                _apply_button_polish(child, role)
            elif isinstance(child, QTableView):
                child.setProperty("visualRole", "settings_table")
                _apply_table_polish(child, policy.table_density)
            elif isinstance(child, QScrollArea):
                child.setProperty("visualRole", "settings_scroll")
        except Exception:
            continue

def apply_runtime_visual_polish(root: QWidget | None, page_id: str, workspace_type: str | None = None) -> None:
    """Apply non-invasive visual normalization to a workspace subtree."""
    if root is None:
        return
    apply_table_direction_tree(root)
    policy = workspace_visual_policy(str(page_id or "workspace"), workspace_type)
    try:
        root.setProperty("visualPageId", policy.page_id)
        root.setProperty("visualWorkspaceType", policy.workspace_type)
        root.setProperty("projectVisualIdentityPhase", str(BRAND.get("project_visual_identity_phase", 447)))
        root.setProperty("visualIdentitySweepPhase", str(BRAND.get("legacy_visual_style_sweep_phase", 447)))
        root.setProperty("visualStyleSource", BRAND.get("workspace_style_source", "centralized_runtime_visual_identity"))
        root.setProperty("visualRole", "workspace_surface")
        _set_if_empty_object_name(root, policy.object_name)
        _layout_apply(root, policy.margin, policy.spacing)
    except Exception:
        pass

    children = list(root.findChildren(QWidget)) if hasattr(root, "findChildren") else []
    for child in children:
        try:
            child.setProperty("visualWorkspaceType", policy.workspace_type)
            child.setProperty("projectVisualIdentityPhase", str(BRAND.get("project_visual_identity_phase", 447)))
            child.setProperty("visualIdentitySweepPhase", str(BRAND.get("legacy_visual_style_sweep_phase", 447)))
            child.setProperty("visualStyleSource", BRAND.get("workspace_style_source", "centralized_runtime_visual_identity"))
            _layout_apply(child, policy.margin, policy.spacing)
            if isinstance(child, QTableView):
                _apply_table_polish(child, policy.table_density)
            elif isinstance(child, QTabWidget):
                child.setProperty("visualRole", "workspace_tabs")
                child.setDocumentMode(True)
            elif isinstance(child, (QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox)):
                _apply_input_polish(child)
            elif isinstance(child, QAbstractButton):
                _apply_button_polish(child, "workspace_action")
            elif isinstance(child, QScrollArea):
                if not child.property("visualRole"):
                    child.setProperty("visualRole", "workspace_scroll")
                try:
                    child.setWidgetResizable(True)
                except Exception:
                    pass
            elif isinstance(child, QStackedWidget):
                if not child.property("visualRole"):
                    child.setProperty("visualRole", "workspace_stack")
            elif isinstance(child, QSplitter):
                if not child.property("visualRole"):
                    child.setProperty("visualRole", "workspace_splitter")
            elif isinstance(child, QLabel):
                name = (child.objectName() or "").lower()
                text = (child.text() or "").strip()
                if "title" in name or "header" in name or len(text) <= 28 and text.endswith((':', '：')):
                    if not child.property("visualRole"):
                        child.setProperty("visualRole", "section_header")
            elif isinstance(child, (QFrame, QGroupBox)):
                if not child.property("visualRole"):
                    child.setProperty("visualRole", "workspace_card")
        except Exception:
            continue

    # Phase447: apply the unified list visual template after generic roles so
    # list-specific controls can override older Basit/list-toolbar styling.
    try:
        _apply_list_workspace_template(root, policy)
    except Exception:
        pass

    # Phase451: apply settings-specific chrome after generic roles and list rules
    # so old Basit/Modern settings styling cannot dominate cards, tabs, notes or inputs.
    try:
        _apply_settings_workspace_template(root, policy)
    except Exception:
        pass

    # Phase453: final Windows screenshot-facing acceptance pass.  It must run
    # after list/settings/document/operational roles so it only fills gaps and
    # performs Arabic label cleanup for controls created by lazy pages.
    try:
        apply_windows_runtime_visual_acceptance(root, policy.page_id, policy.workspace_type)
        # Phase454: reconstruct dense Runtime layouts after the Windows acceptance polish.
        apply_runtime_layout_reconstruction(root, policy.page_id, policy.workspace_type)
        # Phase455: targeted rebuild for the screenshot-problem screens.
        apply_targeted_screen_rebuild(root, policy.page_id, policy.workspace_type)
        # Phase456: harden the rebuilt single screens against Windows runtime regressions.
        apply_single_screen_runtime_hardening(root, policy.page_id, policy.workspace_type)
        # Phase457: gate the Phase453-456 chain and expose a deterministic regression signature.
        apply_runtime_visual_regression_gate(root, policy.page_id, policy.workspace_type)
    except Exception:
        pass

    # Dynamic-property QSS selectors need a repolish after the pass.
    try:
        root.style().unpolish(root)
        root.style().polish(root)
        root.update()
    except Exception:
        pass
    try:
        QTimer.singleShot(0, root.update)
    except Exception:
        pass


__all__ = ["apply_runtime_visual_polish"]
