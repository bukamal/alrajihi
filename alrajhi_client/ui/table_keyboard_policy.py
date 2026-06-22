# -*- coding: utf-8 -*-
"""Unified keyboard policy for editable ERP tables.

Phase 337 standardizes the high-throughput workflow expected by cashiers,
accountants, warehouse operators, and restaurant/cafe/apparel users:

* Enter on an editable cell starts editing.
* Enter after committing an editor moves to the next editable visible cell.
* Shift+Enter moves to the previous editable visible cell.
* At the end of an editable model that exposes ``add_empty_line()``, a new line
  is appended and focus moves to its first editable visible cell.
* Esc is not consumed unless a native editor is already active; the application
  level Esc-to-dashboard shortcut remains in control elsewhere.

The mixin intentionally contains no business logic and no database access.  It
only speaks Qt's model/view protocol and can be applied to QTableView and
QTableWidget based grids.
"""
from __future__ import annotations

from typing import Iterable

from PyQt5.QtCore import QModelIndex, QTimer, Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QAbstractItemDelegate, QAbstractItemView


class StandardTableKeyboardMixin:
    """Mixin for QAbstractItemView subclasses used as ERP entry grids."""

    _standard_keyboard_active: bool = False

    def init_standard_table_keyboard(self) -> None:
        """Enable the shared Enter/Shift+Enter table policy on this view."""
        if getattr(self, "_standard_keyboard_active", False):
            return
        self._standard_keyboard_active = True
        try:
            self.setProperty("standard_table_keyboard", True)
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

    def _standard_append_empty_line_if_supported(self) -> bool:
        model = self._standard_model()
        if model is None:
            return False
        target = model
        # SmartTableView may use a proxy. Transaction entry models are normally
        # attached directly, but this keeps the policy safe for filtered grids.
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
            return self._standard_first_editable_index()
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
                    editable = self._standard_editable_columns(row_count - 1)
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

    def _standard_focus_index(self, index: QModelIndex, start_edit: bool = False) -> bool:
        if not index.isValid():
            return False
        try:
            self.setCurrentIndex(index)
            self.scrollTo(index)
            if start_edit and self._standard_is_editable(index):
                QTimer.singleShot(0, lambda idx=index: self.edit(idx))
            return True
        except Exception:
            return False

    def _standard_handle_enter_key(self, event: QKeyEvent) -> bool:
        key = event.key()
        if key not in (Qt.Key_Return, Qt.Key_Enter):
            return False
        # If a native editor currently owns the key, let Qt finish commit/close.
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
                return True
            except Exception:
                return False
        next_index = self._standard_next_index(current, forward=True)
        if next_index.isValid() and next_index != current:
            return self._standard_focus_index(next_index, start_edit=True)
        return False

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
