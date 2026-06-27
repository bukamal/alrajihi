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
    QComboBox,
    QFrame,
    QGroupBox,
    QHeaderView,
    QLineEdit,
    QPlainTextEdit,
    QSizePolicy,
    QSpinBox,
    QDoubleSpinBox,
    QTableView,
    QTableWidget,
    QStyledItemDelegate,
    QTextEdit,
    QWidget,
)

from theme.brand import BRAND
from workspace.runtime.visual_polish_contract import workspace_visual_policy
from ui.table_direction_policy import apply_table_direction, apply_table_direction_tree


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


def apply_runtime_visual_polish(root: QWidget | None, page_id: str, workspace_type: str | None = None) -> None:
    """Apply non-invasive visual normalization to a workspace subtree."""
    if root is None:
        return
    apply_table_direction_tree(root)
    policy = workspace_visual_policy(str(page_id or "workspace"), workspace_type)
    try:
        root.setProperty("visualPageId", policy.page_id)
        root.setProperty("visualWorkspaceType", policy.workspace_type)
        _set_if_empty_object_name(root, policy.object_name)
        _layout_apply(root, policy.margin, policy.spacing)
    except Exception:
        pass

    children = list(root.findChildren(QWidget)) if hasattr(root, "findChildren") else []
    for child in children:
        try:
            child.setProperty("visualWorkspaceType", policy.workspace_type)
            _layout_apply(child, policy.margin, policy.spacing)
            if isinstance(child, QTableView):
                _apply_table_polish(child, policy.table_density)
            elif isinstance(child, (QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox)):
                _apply_input_polish(child)
            elif isinstance(child, QAbstractButton):
                _apply_button_polish(child, policy.button_role)
            elif isinstance(child, (QFrame, QGroupBox)):
                child.setProperty("visualRole", policy.card_role)
        except Exception:
            continue

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
