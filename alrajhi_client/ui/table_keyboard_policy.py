# -*- coding: utf-8 -*-
"""Unified keyboard policy for editable ERP tables.

Phase 337 standardized Enter/Shift+Enter traversal.  Phase 348 extends the
same policy to entry focus and editor text handling:

* Any editable document/grid can request initial focus on the material/item
  column instead of a random header/input.
* The preferred entry column is resolved by schema key first (``item``,
  ``material``, ``product``, ``barcode``), then by translated header text.
* Enter opens the editor and selects existing text for replacement only when
  the operator starts typing; navigation itself does not clear cell values.
* Phase382 added a runtime flow contract: material/barcode -> quantity.
* Phase385 refines the operational sequence to item/barcode -> unit -> quantity,
  so operators can confirm the unit before quantity while preserving the same
  barcode/material resolver and newly inserted-line focus.
* Phase386 replaces physical-column Enter walking in sales/purchase invoices
  with a business route: material -> unit -> quantity -> price -> discount ->
  tax/total -> notes.  Enter traversal selects or focuses cells only; it never
  clears existing values merely because the operator is moving through the row.
* Phase388 prevents mouse-triggered focus loss from being interpreted as
  Enter navigation.  Clicking side actions such as edit/delete/print must
  close the active cell editor without moving to the next grid cell.
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
    _standard_material_entry_keys = ("item", "material", "product")
    _standard_barcode_entry_keys = ("barcode",)
    _standard_unit_entry_keys = ("unit", "uom", "unit_name")
    _standard_quantity_entry_keys = ("qty", "quantity", "return_qty", "required_qty")
    _standard_default_editor_tokens = {"", "0", "0.0", "0.00", "0.000"}
    _standard_navigation_clear_placeholders = False

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
        self._standard_editor_close_navigation: str | None = None

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

    def _standard_entry_priority(self, column: int) -> int:
        """Priority for initial entry columns; material/item beats barcode."""
        key = self._standard_column_key(column).strip().casefold()
        priority_keys = {name.casefold(): pos for pos, name in enumerate(self._standard_preferred_entry_keys)}
        if key in priority_keys:
            return priority_keys[key]
        header_priorities = (
            (0, ("مادة", "المادة", "الصنف", "item", "material", "artikel")),
            (1, ("منتج", "product", "produkt")),
            (2, ("باركود", "barcode")),
        )
        for priority, tokens in header_priorities:
            if any(token in key for token in tokens):
                return priority
        return 999

    def _standard_entry_columns(self, row: int) -> list[int]:
        editable = self._standard_editable_columns(row)
        preferred = [c for c in editable if self._standard_is_preferred_entry_column(c)]
        if preferred:
            return sorted(preferred, key=lambda c: (self._standard_entry_priority(c), c))
        return editable

    def _standard_columns_matching_keys(self, row: int, keys: tuple[str, ...]) -> list[int]:
        """Return editable visible columns in *row* matching one of ``keys``."""
        wanted = {str(key or "").casefold() for key in keys}
        matches: list[int] = []
        for col in self._standard_editable_columns(row):
            key = self._standard_column_key(col).strip().casefold()
            if key in wanted:
                matches.append(col)
        return matches

    def _standard_entry_index_for_row(self, row: int) -> QModelIndex:
        model = self._standard_model()
        if model is None or row < 0:
            return QModelIndex()
        try:
            if row >= model.rowCount():
                return QModelIndex()
        except Exception:
            return QModelIndex()
        cols = self._standard_entry_columns(row)
        if cols:
            return model.index(row, cols[0])
        return QModelIndex()

    def _standard_last_entry_index(self) -> QModelIndex:
        model = self._standard_model()
        if model is None:
            return QModelIndex()
        try:
            row = model.rowCount() - 1
        except Exception:
            row = -1
        while row >= 0:
            idx = self._standard_entry_index_for_row(row)
            if idx.isValid():
                return idx
            row -= 1
        return QModelIndex()

    def _standard_is_traversable(self, index: QModelIndex) -> bool:
        """Return True when Enter may stop on the cell.

        Editable cells are traversable.  Read-only calculated cells such as
        ``total`` are also traversable so operators can visually confirm the
        result before Enter continues to notes or the next row.
        """
        if not index.isValid():
            return False
        flags = self._standard_flags(index)
        return bool(flags & Qt.ItemIsEnabled) and bool(flags & Qt.ItemIsSelectable)

    def _standard_business_route_slots(self) -> list[tuple[str, ...]]:
        """Return the invoice-specific Enter route expressed as key aliases.

        The route is deliberately semantic, not physical.  Purchase grids keep
        the storage key ``cost`` for accounting compatibility but expose it in
        the operator route as the visible price cell.  Batch/expiry and other
        side columns stay reachable by mouse/Tab/column navigation, but Enter
        follows the fast invoice-entry path requested for daily data entry.
        """
        model = self._standard_source_model() or self._standard_model()
        columns = getattr(model, "columns", None)
        if not columns:
            return []
        keys = []
        for column in columns:
            try:
                keys.append(str(column.key or "").strip().casefold())
            except Exception:
                pass
        key_set = set(keys)
        invoice_core = {"item", "unit", "qty", "discount", "total", "notes"}
        if not invoice_core.issubset(key_set):
            return []
        if "cost" in key_set and "price" not in key_set:
            return [("item", "material", "product", "barcode"), ("unit", "uom", "unit_name"), ("qty", "quantity"), ("cost", "price"), ("discount",), ("tax",), ("total",), ("notes",)]
        if "price" in key_set:
            return [("item", "material", "product", "barcode"), ("unit", "uom", "unit_name"), ("qty", "quantity"), ("price",), ("discount",), ("total",), ("notes",)]
        return []

    def _standard_route_column_for_slot(self, row: int, slot: tuple[str, ...]) -> int | None:
        wanted = {str(key or "").casefold() for key in slot}
        model = self._standard_model()
        if model is None or row < 0:
            return None
        try:
            count = model.columnCount()
        except Exception:
            count = 0
        # Preserve the semantic order inside aliases.  This is critical for the
        # first invoice slot where both ``item`` and ``barcode`` can exist: the
        # initial Enter path must start at the material column, not at barcode.
        ordered_wanted = [str(key or "").casefold() for key in slot]
        for wanted_key in ordered_wanted:
            if wanted_key not in wanted:
                continue
            for col in range(count):
                if self._standard_column_hidden(col):
                    continue
                key = self._standard_column_key(col).strip().casefold()
                if key != wanted_key:
                    continue
                try:
                    index = model.index(row, col)
                except Exception:
                    continue
                if self._standard_is_traversable(index):
                    return col
        return None

    def _standard_business_route_columns(self, row: int) -> list[int]:
        route: list[int] = []
        for slot in self._standard_business_route_slots():
            col = self._standard_route_column_for_slot(row, slot)
            if col is not None and col not in route:
                route.append(col)
        return route

    def _standard_next_business_route_index(self, start: QModelIndex, forward: bool = True) -> QModelIndex:
        """Move by the sales/purchase business route when available."""
        model = self._standard_model()
        if model is None or not start.isValid():
            return QModelIndex()
        row = start.row()
        route = self._standard_business_route_columns(row)
        if not route:
            return QModelIndex()
        current_col = start.column()
        if current_col not in route:
            current_key = self._standard_column_key(current_col).strip().casefold()
            if current_key == "barcode":
                current_col = route[0]
            else:
                return QModelIndex()
        try:
            pos = route.index(current_col)
        except ValueError:
            return QModelIndex()
        if forward:
            for col in route[pos + 1:]:
                return model.index(row, col)
            if self._standard_append_empty_line_if_supported():
                try:
                    new_row = model.rowCount() - 1
                except Exception:
                    new_row = -1
                if new_row >= 0:
                    new_route = self._standard_business_route_columns(new_row)
                    if new_route:
                        return model.index(new_row, new_route[0])
            return start
        for col in reversed(route[:pos]):
            return model.index(row, col)
        if row > 0:
            prev_route = self._standard_business_route_columns(row - 1)
            if prev_route:
                return model.index(row - 1, prev_route[-1])
        return start

    def _standard_post_commit_index(self, start: QModelIndex) -> QModelIndex:
        """Choose the next operational cell after a barcode/material commit.

        Phase385 ERP line-entry flow is material/barcode -> unit -> quantity.
        If the unit column is hidden or locked, the fallback remains quantity.
        Price and later columns stay reachable through normal Enter traversal.
        """
        if not start.isValid():
            return QModelIndex()
        current_key = self._standard_column_key(start.column()).strip().casefold()
        entry_keys = {*(key.casefold() for key in self._standard_material_entry_keys), *(key.casefold() for key in self._standard_barcode_entry_keys)}
        if current_key not in entry_keys:
            return QModelIndex()
        route_target = self._standard_next_business_route_index(start, forward=True)
        if route_target.isValid() and route_target != start:
            return route_target
        unit_cols = self._standard_columns_matching_keys(start.row(), self._standard_unit_entry_keys)
        if unit_cols:
            return self._standard_model().index(start.row(), unit_cols[0])
        qty_cols = self._standard_columns_matching_keys(start.row(), self._standard_quantity_entry_keys)
        if qty_cols:
            return self._standard_model().index(start.row(), qty_cols[0])
        return QModelIndex()

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

    def focus_entry_column(self, start_edit: bool = True, row: int | None = None) -> bool:
        """Move focus to the material/item entry cell in the table.

        ``row`` is optional: first row for document open, newly inserted row for
        add-line actions.  Keeping this in the table policy avoids each document
        reimplementing a slightly different focus path.
        """
        try:
            self.setFocus(Qt.OtherFocusReason)
        except Exception:
            pass
        index = self._standard_entry_index_for_row(row) if row is not None else self._standard_first_entry_index()
        return self._standard_focus_index(index, start_edit=start_edit)

    def focus_last_entry_column(self, start_edit: bool = True) -> bool:
        """Move focus to the newest line's material/item entry cell."""
        try:
            self.setFocus(Qt.OtherFocusReason)
        except Exception:
            pass
        return self._standard_focus_index(self._standard_last_entry_index(), start_edit=start_edit)

    def schedule_initial_entry_focus(self, delay: int = 80, start_edit: bool = True, row: int | None = None) -> None:
        """Schedule grid focus after the model/layout becomes visible."""
        if not getattr(self, "_standard_keyboard_active", False):
            return
        QTimer.singleShot(delay, lambda: self.focus_entry_column(start_edit=start_edit, row=row))

    def schedule_last_entry_focus(self, delay: int = 80, start_edit: bool = True) -> None:
        """Schedule focus on the latest inserted line."""
        if not getattr(self, "_standard_keyboard_active", False):
            return
        QTimer.singleShot(delay, lambda: self.focus_last_entry_column(start_edit=start_edit))

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

        route_target = self._standard_next_business_route_index(start, forward=forward)
        if route_target.isValid() and route_target != start:
            return route_target

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
        """Prepare the active editor without erasing data while navigating.

        Phase384: Enter navigation must not clear existing/default values merely
        because focus moved into a cell.  The editor selects its text so genuine
        new typing naturally replaces it, while moving through cells preserves the
        displayed content until the operator actually enters a new value.
        """
        editor = self._standard_editor_widget()
        if editor is None:
            return
        try:
            if isinstance(editor, QLineEdit):
                editor.setAlignment(Qt.AlignCenter)
                editor.selectAll()
            elif isinstance(editor, QTextEdit):
                editor.selectAll()
            elif isinstance(editor, QPlainTextEdit):
                editor.selectAll()
            try:
                already = bool(editor.property("standard_enter_commit_filter"))
            except Exception:
                already = False
            if not already:
                editor.installEventFilter(self)
                try:
                    editor.setProperty("standard_enter_commit_filter", True)
                except Exception:
                    pass
        except Exception:
            pass

    def eventFilter(self, obj, event):  # type: ignore[override]
        try:
            if (
                getattr(self, "_standard_keyboard_active", False)
                and getattr(obj, "property", lambda _name: False)("standard_enter_commit_filter")
                and isinstance(event, QKeyEvent)
                and event.key() in (Qt.Key_Return, Qt.Key_Enter)
            ):
                current = self._standard_index()
                if event.modifiers() & Qt.ShiftModifier:
                    try:
                        self._standard_editor_close_navigation = "previous"
                        self.commitData(obj)
                        self.closeEditor(obj, QAbstractItemDelegate.EditPreviousItem)
                    except Exception:
                        self._standard_editor_close_navigation = None
                        self._standard_focus_index(self._standard_next_index(current, False), start_edit=True)
                    return True
                try:
                    self._standard_editor_close_navigation = "next"
                    self.commitData(obj)
                    self.closeEditor(obj, QAbstractItemDelegate.NoHint)
                    return True
                except Exception:
                    self._standard_editor_close_navigation = None
                    self._standard_focus_index(self._standard_next_index(current, True), start_edit=True)
                    return True
        except Exception:
            self._standard_editor_close_navigation = None
        try:
            return super().eventFilter(obj, event)
        except Exception:
            return False

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

    def _standard_editor_close_should_navigate(self, hint) -> str | None:
        """Return the requested Enter route direction for an editor close.

        Closing an editor because the operator clicked a side action button
        (edit/delete/print/save and similar controls) must not be treated like
        Enter.  Qt reports that focus-loss close mostly as ``NoHint``; older
        code interpreted every ``NoHint`` as a request to move to the next cell,
        which stole the mouse click from the side button and reopened the grid
        editor.  Only Enter/Shift+Enter sets ``_standard_editor_close_navigation``.
        """
        pending = getattr(self, "_standard_editor_close_navigation", None)
        if pending in {"next", "previous"}:
            return pending
        if hint == QAbstractItemDelegate.EditPreviousItem:
            return "previous"
        if hint == QAbstractItemDelegate.EditNextItem:
            return "next"
        # NoHint/SubmitModelCache may be focus-out, mouse click, model reset, or
        # dialog opening.  Do not auto-step unless our Enter handler explicitly
        # requested it via the pending flag above.
        return None

    def closeEditor(self, editor, hint):  # type: ignore[override]
        current = self._standard_index()
        direction = self._standard_editor_close_should_navigate(hint)
        try:
            super().closeEditor(editor, hint)
        finally:
            self._standard_editor_close_navigation = None
        if not getattr(self, "_standard_keyboard_active", False) or direction is None:
            return
        if direction == "previous":
            QTimer.singleShot(0, lambda: self._standard_focus_index(self._standard_next_index(current, False), start_edit=True))
            return

        def _focus_after_commit(idx=current):
            target = self._standard_post_commit_index(idx)
            if target.isValid():
                self._standard_focus_index(target, start_edit=True)
                return
            self._standard_focus_index(self._standard_next_index(idx, True), start_edit=True)
        QTimer.singleShot(0, _focus_after_commit)
