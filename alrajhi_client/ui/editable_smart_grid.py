# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QHeaderView,
    QInputDialog,
    QMenu,
    QMessageBox,
    QTableWidget,
)

from i18n import translate
from views.widgets.components.table_preferences import TablePreferences


class EditableSmartGrid(QTableWidget):
    """Standard editable grid for ERP line-entry tables.

    SmartTableView is the standard for read-only/model-backed tables. Some ERP
    screens still require cell widgets and immediate in-place edits (invoice
    lines, returns, POS, unit conversions, settings matrices). This class keeps
    those screens editable while providing the same enterprise table behaviors:
    column moving, hide/show, layout persistence, responsive widths, copy, and
    a unified context menu.
    """

    def __init__(self, *args, identity: Optional[str] = None, parent=None):
        # Preserve QTableWidget constructor compatibility: (rows, columns, parent)
        if parent is not None and (not args or args[-1] is not parent):
            args = (*args, parent)
        super().__init__(*args)
        self._preferences = TablePreferences()
        self._layout_save_pending = False
        self._restoring_layout = False
        self._auto_fit_columns = True
        self._density = "comfortable"
        if identity:
            self.set_table_identity(identity)
        elif not self.objectName():
            self.setObjectName("EditableSmartGrid")
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)
        self.horizontalHeader().setSectionsMovable(True)
        self.horizontalHeader().setSectionsClickable(True)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setMinimumSectionSize(64)
        self.horizontalHeader().setDefaultSectionSize(132)
        self.horizontalHeader().sectionResized.connect(self._schedule_save_layout)
        self.horizontalHeader().sectionMoved.connect(lambda *args: self._schedule_save_layout())
        self.verticalHeader().setDefaultSectionSize(34)
        self.setWordWrap(False)
        self._install_shortcuts()
        QTimer.singleShot(0, self.restore_layout)

    def set_table_identity(self, identity: str) -> None:
        if identity:
            self.setObjectName(identity)
            QTimer.singleShot(0, self.restore_layout)

    def _layout_key(self) -> str:
        parent = self.parent()
        parent_name = parent.__class__.__name__ if parent is not None else "root"
        return f"editable_grids/{parent_name}/{self.objectName() or self.__class__.__name__}"

    def _install_shortcuts(self) -> None:
        actions = [
            (QKeySequence.Copy, self.copy_selection),
            (QKeySequence("Ctrl+Shift+C"), self.show_column_chooser),
            (QKeySequence("Ctrl+Shift+F"), self.fit_columns_to_view),
            (QKeySequence("Ctrl+Shift+S"), lambda: self.save_view_preset()),
        ]
        for seq, callback in actions:
            act = QAction(self)
            act.setShortcut(seq)
            act.setShortcutContext(Qt.WidgetWithChildrenShortcut)
            act.triggered.connect(callback)
            self.addAction(act)

    def setHorizontalHeaderLabels(self, labels):  # type: ignore[override]
        super().setHorizontalHeaderLabels(labels)
        self.restore_layout()
        if self._auto_fit_columns:
            QTimer.singleShot(0, self.fit_columns_to_view)

    def setColumnCount(self, columns: int) -> None:  # type: ignore[override]
        super().setColumnCount(columns)
        self.restore_layout()
        if self._auto_fit_columns:
            QTimer.singleShot(0, self.fit_columns_to_view)

    def setRowCount(self, rows: int) -> None:  # type: ignore[override]
        super().setRowCount(rows)
        if self._auto_fit_columns:
            QTimer.singleShot(0, self.fit_columns_to_view)

    def _schedule_save_layout(self, *args) -> None:
        if self._restoring_layout or self._layout_save_pending:
            return
        self._layout_save_pending = True
        QTimer.singleShot(250, self.save_layout)

    def save_layout(self) -> None:
        self._layout_save_pending = False
        if self.columnCount() <= 0:
            return
        self._preferences.save_state(self._layout_key(), self.horizontalHeader().saveState())
        self._preferences.save_value(self._layout_key(), "density", self._density)
        self._preferences.save_value(self._layout_key(), "responsive", bool(self._auto_fit_columns))

    def restore_layout(self) -> None:
        if self.columnCount() <= 0:
            return
        self._restoring_layout = True
        try:
            state = self._preferences.load_state(self._layout_key())
            if state:
                self.horizontalHeader().restoreState(state)
            self._auto_fit_columns = bool(self._preferences.load_value(self._layout_key(), "responsive", self._auto_fit_columns))
            self.set_density(str(self._preferences.load_value(self._layout_key(), "density", self._density)))
        finally:
            self._restoring_layout = False
        if self._auto_fit_columns:
            QTimer.singleShot(0, self.fit_columns_to_view)

    def reset_layout(self) -> None:
        self._preferences.reset(self._layout_key())
        for col in range(self.columnCount()):
            self.setColumnHidden(col, False)
            self.horizontalHeader().setSectionResizeMode(col, QHeaderView.Interactive)
        self.fit_columns_to_view()
        self.save_layout()

    def visible_columns(self):
        return [col for col in range(self.columnCount()) if not self.isColumnHidden(col)]

    def set_column_visible(self, column: int, visible: bool) -> None:
        if not visible and len(self.visible_columns()) <= 1:
            return
        self.setColumnHidden(column, not visible)
        self.save_layout()
        if self._auto_fit_columns:
            QTimer.singleShot(0, self.fit_columns_to_view)

    def show_column_chooser(self) -> None:
        menu = QMenu(self)
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            title = header_item.text() if header_item else f"{col + 1}"
            act = QAction(title, self)
            act.setCheckable(True)
            act.setChecked(not self.isColumnHidden(col))
            act.toggled.connect(lambda checked, c=col: self.set_column_visible(c, checked))
            menu.addAction(act)
        menu.addSeparator()
        reset = QAction(translate("reset_columns") if translate("reset_columns") != "reset_columns" else "Reset columns", self)
        reset.triggered.connect(self.reset_layout)
        menu.addAction(reset)
        menu.exec(self.mapToGlobal(self.rect().center()))

    def set_responsive_columns(self, enabled: bool = True) -> None:
        self._auto_fit_columns = bool(enabled)
        if enabled:
            self.fit_columns_to_view()
        self.save_layout()

    def fit_columns_to_view(self) -> None:
        if self.columnCount() <= 0 or not self._auto_fit_columns:
            return
        visible = self.visible_columns()
        if not visible:
            return
        viewport_width = max(320, self.viewport().width())
        minimum = 72
        fixed_width = 0
        flexible = []
        for col in visible:
            header_item = self.horizontalHeaderItem(col)
            header = (header_item.text() if header_item else "").lower()
            if any(key in header for key in ("id", "#", "no", "رقم")) or len(header) <= 3:
                width = max(minimum, min(96, self.columnWidth(col) or 84))
                self.setColumnWidth(col, width)
                fixed_width += width
            else:
                flexible.append(col)
        if not flexible:
            return
        per_col = max(minimum, int((viewport_width - fixed_width - 24) / max(1, len(flexible))))
        for col in flexible:
            self.setColumnWidth(col, per_col)

    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        if self._auto_fit_columns:
            QTimer.singleShot(0, self.fit_columns_to_view)

    def set_density(self, density: str) -> None:
        density = (density or "comfortable").strip().lower()
        sizes = {"compact": 28, "comfortable": 34, "touch": 44}
        if density not in sizes:
            density = "comfortable"
        self._density = density
        self.verticalHeader().setDefaultSectionSize(sizes[density])
        self.setProperty("density", density)

    def copy_selection(self) -> None:
        selection = self.selectedIndexes()
        if not selection:
            return
        rows = sorted({i.row() for i in selection})
        cols = sorted({i.column() for i in selection})
        out = []
        for row in rows:
            values = []
            for col in cols:
                item = self.item(row, col)
                values.append(item.text() if item else "")
            out.append("\t".join(values))
        QApplication.clipboard().setText("\n".join(out))

    def save_view_preset(self, name: Optional[str] = None) -> None:
        name = (name or "").strip()
        if not name:
            name, ok = QInputDialog.getText(self, translate("save_view") if translate("save_view") != "save_view" else "Save view", translate("view_name") if translate("view_name") != "view_name" else "View name")
            if not ok or not name.strip():
                return
            name = name.strip()
        self.save_layout()
        self._preferences.save_named_view(self._layout_key(), name, self.horizontalHeader().saveState(), {}, bool(self._auto_fit_columns))

    def apply_view_preset(self, name: str) -> None:
        preset = self._preferences.load_named_view(self._layout_key(), name)
        if not preset:
            return
        state = preset.get("header_state")
        if state:
            self.horizontalHeader().restoreState(state)
        self.set_responsive_columns(bool(preset.get("responsive", self._auto_fit_columns)))

    def view_preset_names(self):
        return self._preferences.named_view_names(self._layout_key())

    def _show_menu(self, pos) -> None:
        menu = QMenu(self)
        copy = QAction(translate("copy") if translate("copy") != "copy" else "Copy", self)
        copy.triggered.connect(self.copy_selection)
        menu.addAction(copy)
        menu.addSeparator()
        columns = QAction(translate("columns") if translate("columns") != "columns" else "Columns", self)
        columns.triggered.connect(self.show_column_chooser)
        menu.addAction(columns)
        fit = QAction(translate("fit_columns") if translate("fit_columns") != "fit_columns" else "Fit columns", self)
        fit.triggered.connect(self.fit_columns_to_view)
        menu.addAction(fit)
        responsive = QAction(translate("responsive_columns") if translate("responsive_columns") != "responsive_columns" else "Responsive columns", self)
        responsive.setCheckable(True)
        responsive.setChecked(self._auto_fit_columns)
        responsive.toggled.connect(self.set_responsive_columns)
        menu.addAction(responsive)
        reset = QAction(translate("reset_columns") if translate("reset_columns") != "reset_columns" else "Reset columns", self)
        reset.triggered.connect(self.reset_layout)
        menu.addAction(reset)
        presets = self.view_preset_names()
        if presets:
            preset_menu = menu.addMenu(translate("view_presets") if translate("view_presets") != "view_presets" else "View presets")
            for preset_name in presets:
                preset_menu.addAction(preset_name, lambda n=preset_name: self.apply_view_preset(n))
        menu.exec(self.viewport().mapToGlobal(pos))
