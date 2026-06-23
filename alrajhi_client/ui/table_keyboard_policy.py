# -*- coding: utf-8 -*-
"""Unified keyboard policy for editable ERP tables.

Phase 337 standardized Enter/Shift+Enter traversal.  Phase 348 extends the
same policy to entry focus and editor text handling:

* Any editable document/grid can request initial focus on the material/item
  column instead of a random header/input.
* The preferred entry column is resolved by schema key first (``item``,
  ``material``, ``product``, ``barcode``), then by translated header text.
* Enter opens the editor and prepares its text so default placeholders such as
  ``0`` or empty values are cleared while real values are selected.
* Shift+Enter still walks backwards.  Esc is not consumed unless a native editor is already active; the application
  level Esc-to-dashboard shortcut remains in control elsewhere.

The mixin intentionally contains no business logic and no database access.  It
only speaks Qt's model/view protocol and can be applied to QTableView and
QTableWidget based grids.
"""
from __future__ import annotations

from typing import Iterable

from PyQt5.QtCore import QModelIndex, QItemSelectionModel, QTimer, Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (
    QApplication,
    QAbstractItemDelegate,
    QAbstractItemView,
    QComboBox,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QDoubleSpinBox,
    QTextEdit,
)


class StandardTableKeyboardMixin:
    """Mixin for QAbstractItemView subclasses used as ERP entry grids."""

    _standard_keyboard_active: bool = False
    _standard_preferred_entry_keys = ("item", "material", "product", "barcode")
    _standard_default_editor_tokens = {"", "0", "0.0", "0.00", "0.000"}

    def init_standard_table_keyboard(self) -> None:
        """Enable the shared Enter/Shift+Enter table policy on this view."""
        if getattr(self, "_standard_keyboard_active", False):
            return
        self._standard_keyboard_active = True
        try:
            self.setProperty("standard_table_keyboard", True)
            self.setProperty("standard_initial_entry_focus", True)
            self.setProperty("current_cell_highlight", True)
            # Phase355: editable grids get the stronger branded current-cell
            # treatment.  List-only grids keep the lighter table skin.
            self.setProperty("brand_entry_table", True)
            # Phase349: entry grids must make the active field visually distinct,
            # not just the whole row.  Item selection lets QSS highlight the exact
            # current cell while still allowing the user to copy a block manually.
            self.setSelectionBehavior(QAbstractItemView.SelectItems)
            self.setSelectionMode(QAbstractItemView.ExtendedSelection)
            self.setEditTriggers(
                QAbstractItemView.DoubleClicked
                | QAbstractItemView.EditKeyPressed
                | QAbstractItemView.AnyKeyPressed
            )
        except Exception:
            pass

    def _standard_model(self):
        try:
            return self.model()
        except Exception:
            return None

    def _standard_source_model(self):
        model = self._standard_model()
        try:
            source = getattr(model, "sourceModel", lambda: None)()
            return source or model
        except Exception:
            return model

    def _standard_index(self) -> QModelIndex:
        try:
            index = self.currentIndex()
            return index if index and index.isValid() else QModelIndex()
        except Exception:
            return QModelIndex()

    def _standard_column_hidden(self, column: int) -> bool:
        try:
            return bool(self.isColumnHidden(column))
        except Exception:
            return False

    def _standard_flags(self, index: QModelIndex):
        model = self._standard_model()
        if model is None or not index.isValid():
            return Qt.NoItemFlags
        try:
            return model.flags(index)
        except Exception:
            return Qt.NoItemFlags

    def _standard_is_editable(self, index: QModelIndex) -> bool:
        return bool(index.isValid() and (self._standard_flags(index) & Qt.ItemIsEditable))

    def _standard_column_key(self, column: int) -> str:
        """Return the stable key/header for a visible table column."""
        for model in (self._standard_source_model(), self._standard_model()):
            if model is None:
                continue
            columns = getattr(model, "columns", None)
            if columns is not None and 0 <= column < len(columns):
                try:
                    return str(columns[column].key or "")
                except Exception:
                    pass
            data_keys = getattr(model, "_data_keys", None)
            if data_keys is not None and 0 <= column < len(data_keys):
                try:
                    return str(data_keys[column] or "")
                except Exception:
                    pass
            try:
                header = model.headerData(column, Qt.Horizontal, Qt.DisplayRole)
                if header not in (None, ""):
                    return str(header)
            except Exception:
                pass
        return str(column)

    def _standard_is_preferred_entry_column(self, column: int) -> bool:
        key = self._standard_column_key(column).strip().casefold()
        if key in {k.casefold() for k in self._standard_preferred_entry_keys}:
            return True
        # Header fallback for older Arabic/English/German tables that do not
        # expose model keys yet.
        return any(
            token in key
            for token in (
                "مادة", "المادة", "الصنف", "منتج", "باركود",
                "item", "material", "product", "barcode",
                "artikel", "produkt", "barcode",
            )
        )

    def _standard_editable_columns(self, row: int) -> list[int]:
        model = self._standard_model()
        if model is None or row < 0:
            return []
        columns = []
        try:
            count = model.columnCount()
        except Exception:
            count = 0
        for col in range(count):
            if self._standard_column_hidden(col):
                continue
            try:
                idx = model.index(row, col)
            except Exception:
                continue
            if self._standard_is_editable(idx):
                columns.append(col)
        return columns

    def _standard_entry_columns(self, row: int) -> list[int]:
        editable = self._standard_editable_columns(row)
        preferred = [c for c in editable if self._standard_is_preferred_entry_column(c)]
        return preferred or editable

    def _standard_first_editable_index(self) -> QModelIndex:
        model = self._standard_model()
        if model is None:
            return QModelIndex()
        try:
            rows = model.rowCount()
        except Exception:
            rows = 0
        for row in range(rows):
            cols = self._standard_editable_columns(row)
            if cols:
                return model.index(row, cols[0])
        return QModelIndex()

    def _standard_first_entry_index(self) -> QModelIndex:
        model = self._standard_model()
        if model is None:
            return QModelIndex()
        try:
            rows = model.rowCount()
        except Exception:
            rows = 0
        for row in range(rows):
            cols = self._standard_entry_columns(row)
            if cols:
                return model.index(row, cols[0])
        return QModelIndex()

    def focus_entry_column(self, start_edit: bool = True) -> bool:
        """Move focus to the first material/item entry cell in the table."""
        try:
            self.setFocus(Qt.OtherFocusReason)
        except Exception:
            pass
        return self._standard_focus_index(self._standard_first_entry_index(), start_edit=start_edit)

    def schedule_initial_entry_focus(self, delay: int = 80, start_edit: bool = True) -> None:
        """Schedule initial grid focus after the model/layout becomes visible."""
        if not getattr(self, "_standard_keyboard_active", False):
            return
        QTimer.singleShot(delay, lambda: self.focus_entry_column(start_edit=start_edit))

    def _standard_append_empty_line_if_supported(self) -> bool:
        model = self._standard_model()
        if model is None:
            return False
        target = model
        try:
            source = getattr(model, "sourceModel", lambda: None)()
            if source is not None:
                target = source
        except Exception:
            pass
        callback = getattr(target, "add_empty_line", None)
        if not callable(callback):
            return False
        try:
            before = int(target.rowCount())
            callback()
            after = int(target.rowCount())
            return after > before
        except Exception:
            return False

    def _standard_next_index(self, start: QModelIndex, forward: bool = True) -> QModelIndex:
        model = self._standard_model()
        if model is None:
            return QModelIndex()
        if not start.isValid():
            return self._standard_first_entry_index() or self._standard_first_editable_index()
        try:
            row_count = model.rowCount()
        except Exception:
            row_count = 0
        if row_count <= 0:
            return QModelIndex()

        row = start.row()
        col = start.column()
        if forward:
            rows: Iterable[int] = range(row, row_count)
            for r in rows:
                editable = self._standard_editable_columns(r)
                if not editable:
                    continue
                for c in editable:
                    if r > row or c > col:
                        return model.index(r, c)
            if self._standard_append_empty_line_if_supported():
                try:
                    row_count = model.rowCount()
                except Exception:
                    row_count = 0
                if row_count:
                    editable = self._standard_entry_columns(row_count - 1)
                    if editable:
                        return model.index(row_count - 1, editable[0])
            return start

        for r in range(row, -1, -1):
            editable = list(reversed(self._standard_editable_columns(r)))
            if not editable:
                continue
            for c in editable:
                if r < row or c < col:
                    return model.index(r, c)
        return start

    def _standard_editor_widget(self):
        try:
            widget = QApplication.focusWidget()
        except Exception:
            return None
        if widget is None:
            return None
        try:
            if isinstance(widget, QComboBox) and widget.isEditable():
                return widget.lineEdit()
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                return widget.findChild(QLineEdit)
            return widget
        except Exception:
            return widget

    def _standard_prepare_active_editor(self, index: QModelIndex) -> None:
        """Select real text and clear placeholder/default values in cell editors."""
        editor = self._standard_editor_widget()
        if editor is None:
            return
        try:
            value = ""
            model = self._standard_model()
            if model is not None and index.isValid():
                value = str(model.data(index, Qt.EditRole) or "").strip()
            if isinstance(editor, QLineEdit):
                if value in self._standard_default_editor_tokens:
                    editor.clear()
                else:
                    editor.selectAll()
            elif isinstance(editor, QTextEdit):
                if value in self._standard_default_editor_tokens:
                    editor.clear()
                else:
                    editor.selectAll()
            elif isinstance(editor, QPlainTextEdit):
                if value in self._standard_default_editor_tokens:
                    editor.clear()
                else:
                    editor.selectAll()
        except Exception:
            pass

    def _standard_focus_index(self, index: QModelIndex, start_edit: bool = False) -> bool:
        if not index.isValid():
            return False
        try:
            self.setCurrentIndex(index)
            try:
                self.selectionModel().select(index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Current)
            except Exception:
                pass
            self.scrollTo(index)
            try:
                self.viewport().update()
            except Exception:
                pass
            if start_edit and self._standard_is_editable(index):
                def _open_editor(idx=index):
                    try:
                        self.edit(idx)
                    except Exception:
                        return
                    QTimer.singleShot(0, lambda idx=idx: self._standard_prepare_active_editor(idx))
                QTimer.singleShot(0, _open_editor)
            return True
        except Exception:
            return False

    def _standard_handle_enter_key(self, event: QKeyEvent) -> bool:
        key = event.key()
        if key not in (Qt.Key_Return, Qt.Key_Enter):
            return False
        try:
            if self.state() == QAbstractItemView.EditingState:
                return False
        except Exception:
            pass
        current = self._standard_index()
        if event.modifiers() & Qt.ShiftModifier:
            return self._standard_focus_index(self._standard_next_index(current, forward=False), start_edit=True)
        if current.isValid() and self._standard_is_editable(current):
            try:
                self.edit(current)
                QTimer.singleShot(0, lambda idx=current: self._standard_prepare_active_editor(idx))
                return True
            except Exception:
                return False
        next_index = self._standard_next_index(current, forward=True)
        if next_index.isValid() and next_index != current:
            return self._standard_focus_index(next_index, start_edit=True)
        return False

    def currentChanged(self, current, previous):  # type: ignore[override]
        try:
            super().currentChanged(current, previous)
        finally:
            try:
                self.viewport().update()
            except Exception:
                pass

    def keyPressEvent(self, event):  # type: ignore[override]
        if self._standard_handle_enter_key(event):
            return
        return super().keyPressEvent(event)

    def closeEditor(self, editor, hint):  # type: ignore[override]
        current = self._standard_index()
        super().closeEditor(editor, hint)
        if not getattr(self, "_standard_keyboard_active", False):
            return
        if hint == QAbstractItemDelegate.EditPreviousItem:
            QTimer.singleShot(0, lambda: self._standard_focus_index(self._standard_next_index(current, False), start_edit=True))
        elif hint in (
            QAbstractItemDelegate.EditNextItem,
            QAbstractItemDelegate.SubmitModelCache,
            QAbstractItemDelegate.NoHint,
        ):
            QTimer.singleShot(0, lambda: self._standard_focus_index(self._standard_next_index(current, True), start_edit=False))
