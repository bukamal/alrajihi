# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional, Dict, List

from PyQt5.QtCore import Qt, QSortFilterProxyModel, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction, QMenu, QHeaderView, QDialog, QVBoxLayout, QHBoxLayout,
    QLineEdit, QCheckBox, QPushButton, QScrollArea, QWidget, QLabel,
    QFormLayout, QComboBox, QMessageBox, QInputDialog
)

from i18n import translate
from views.custom_table_view import CustomTableView


class SmartTableProxyModel(QSortFilterProxyModel):
    """Client-side search/filter proxy used by SmartTableView.

    Phase 61 extends the local proxy from plain text search to a small
    enterprise table filter engine: global search + per-column contains filters.
    Heavy screens may still use service-side filtering; this proxy is optional
    and never introduces data access into the UI layer.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterKeyColumn(-1)
        self._search_text = ""
        self._column_filters: Dict[int, str] = {}

    def set_search_text(self, text: str) -> None:
        self._search_text = (text or "").strip().lower()
        self.invalidateFilter()

    def set_column_filters(self, filters: Dict[int, str]) -> None:
        self._column_filters = {int(k): str(v).strip().lower() for k, v in (filters or {}).items() if str(v).strip()}
        self.invalidateFilter()

    def column_filters(self) -> Dict[int, str]:
        return dict(self._column_filters)

    def filterAcceptsRow(self, source_row, source_parent):  # type: ignore[override]
        model = self.sourceModel()
        if model is None:
            return True
        column_count = model.columnCount(source_parent)
        if self._search_text:
            any_match = False
            for col in range(column_count):
                idx = model.index(source_row, col, source_parent)
                value = str(model.data(idx, Qt.DisplayRole) or "").lower()
                if self._search_text in value:
                    any_match = True
                    break
            if not any_match:
                return False
        for col, needle in self._column_filters.items():
            if col < 0 or col >= column_count:
                continue
            idx = model.index(source_row, col, source_parent)
            value = str(model.data(idx, Qt.DisplayRole) or "").lower()
            if needle not in value:
                return False
        return True


class ColumnChooserDialog(QDialog):
    """Compact column chooser used by every SmartTableView."""

    def __init__(self, table: "SmartTableView") -> None:
        super().__init__(table)
        self.table = table
        self.setWindowTitle(translate("columns") if translate("columns") != "columns" else "Columns")
        self.setMinimumWidth(320)
        self._checks: List[tuple[int, QCheckBox]] = []

        layout = QVBoxLayout(self)
        info = QLabel(translate("column_chooser_hint") if translate("column_chooser_hint") != "column_chooser_hint" else "Show, hide, and reorder columns by dragging table headers.")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.search = QLineEdit()
        self.search.setPlaceholderText(translate("search") if translate("search") != "search" else "Search")
        self.search.textChanged.connect(self._filter_checks)
        layout.addWidget(self.search)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        self.body_layout = QVBoxLayout(body)
        self.body_layout.setContentsMargins(8, 8, 8, 8)
        self.body_layout.setSpacing(6)
        scroll.setWidget(body)
        layout.addWidget(scroll, 1)

        self._build_checks()

        buttons = QHBoxLayout()
        show_all = QPushButton(translate("show_all_columns") if translate("show_all_columns") != "show_all_columns" else "Show all")
        reset = QPushButton(translate("reset_columns") if translate("reset_columns") != "reset_columns" else "Reset")
        close_btn = QPushButton(translate("close") if translate("close") != "close" else "Close")
        show_all.clicked.connect(self._show_all)
        reset.clicked.connect(self.table.reset_layout)
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(show_all)
        buttons.addWidget(reset)
        buttons.addStretch(1)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

    def _build_checks(self) -> None:
        model = self.table.model()
        if not model:
            return
        for col in range(model.columnCount()):
            header = model.headerData(col, Qt.Horizontal, Qt.DisplayRole) or translate("column_number", number=col + 1)
            check = QCheckBox(str(header))
            check.setChecked(not self.table.isColumnHidden(col))
            check.toggled.connect(lambda checked, c=col: self.table.set_column_visible(c, checked))
            self._checks.append((col, check))
            self.body_layout.addWidget(check)
        self.body_layout.addStretch(1)

    def _filter_checks(self, text: str) -> None:
        needle = (text or "").strip().lower()
        for _col, check in self._checks:
            check.setVisible(not needle or needle in check.text().lower())

    def _show_all(self) -> None:
        for _col, check in self._checks:
            check.setChecked(True)


class FilterBuilderDialog(QDialog):
    """Small per-column filter builder for SmartTableView.

    It deliberately implements contains-filters only. That keeps it predictable
    and fast for the current GenericTableModel based screens while creating the
    UX surface needed for future typed filters.
    """

    def __init__(self, table: "SmartTableView") -> None:
        super().__init__(table)
        self.table = table
        self.setWindowTitle(translate("advanced_filters") if translate("advanced_filters") != "advanced_filters" else "Advanced filters")
        self.setMinimumWidth(440)
        self._inputs: Dict[int, QLineEdit] = {}

        layout = QVBoxLayout(self)
        hint = QLabel(translate("advanced_filters_hint") if translate("advanced_filters_hint") != "advanced_filters_hint" else "Filter any visible column. Empty fields are ignored.")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        form = QFormLayout(body)
        form.setContentsMargins(8, 8, 8, 8)
        form.setSpacing(8)
        model = table.source_model() or table.model()
        current = table.column_filters()
        if model:
            for col in range(model.columnCount()):
                if table.isColumnHidden(col):
                    continue
                header = str(model.headerData(col, Qt.Horizontal, Qt.DisplayRole) or col + 1)
                edit = QLineEdit()
                edit.setClearButtonEnabled(True)
                edit.setText(current.get(col, ""))
                edit.setPlaceholderText(translate("contains") if translate("contains") != "contains" else "contains...")
                self._inputs[col] = edit
                form.addRow(header, edit)
        scroll.setWidget(body)
        layout.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        apply_btn = QPushButton(translate("apply") if translate("apply") != "apply" else "Apply")
        clear_btn = QPushButton(translate("clear_filters") if translate("clear_filters") != "clear_filters" else "Clear filters")
        close_btn = QPushButton(translate("close") if translate("close") != "close" else "Close")
        apply_btn.clicked.connect(self._apply)
        clear_btn.clicked.connect(self._clear)
        close_btn.clicked.connect(self.reject)
        buttons.addWidget(clear_btn)
        buttons.addStretch(1)
        buttons.addWidget(apply_btn)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

    def _apply(self) -> None:
        filters = {col: edit.text() for col, edit in self._inputs.items() if edit.text().strip()}
        self.table.set_column_filters(filters)
        self.accept()

    def _clear(self) -> None:
        for edit in self._inputs.values():
            edit.clear()
        self.table.clear_filters()
        self.accept()


class SmartTableView(CustomTableView):
    """Unified ERP table widget for management tabs."""

    def __init__(self, parent=None, identity: Optional[str] = None) -> None:
        super().__init__(parent)
        self._source_model = None
        self._proxy_model = SmartTableProxyModel(self)
        self._local_filter_text = ""
        self._column_filters: Dict[int, str] = {}
        if identity:
            self.set_table_identity(identity)
        self.setObjectName(identity or self.objectName() or "SmartTableView")
        self.setSortingEnabled(True)
        self.setWordWrap(False)
        self.verticalHeader().setDefaultSectionSize(34)
        self.horizontalHeader().setSectionsClickable(True)
        self.horizontalHeader().setSectionsMovable(True)
        self.horizontalHeader().setStretchLastSection(False)
        self._auto_fit_columns = True
        self._minimum_interactive_width = 72
        self._density = 'comfortable'
        self.apply_enterprise_defaults()
        self._install_enterprise_shortcuts()
        self.setStyleSheet(self.styleSheet() + """
            QTableView#SmartTableView, QTableView {
                gridline-color: palette(mid);
                alternate-background-color: palette(alternate-base);
            }
            QHeaderView::section {
                min-height: 30px;
                font-weight: 800;
                padding: 6px 8px;
            }
        """)


    def _install_enterprise_shortcuts(self) -> None:
        """Install table-level shortcuts expected across ERP grids.

        These shortcuts deliberately call existing SmartTable APIs. They do not
        bypass services, printing, or export paths; they only make table work
        faster for keyboard-heavy invoice, stock, report, and accounting users.
        """
        shortcuts = [
            ("Ctrl+Shift+C", self.show_column_chooser),
            ("Ctrl+Shift+F", self.fit_columns_to_view),
            ("Ctrl+Alt+F", self.show_filter_builder),
            ("Ctrl+Shift+S", lambda: self.save_view_preset()),
        ]
        for key, callback in shortcuts:
            action = QAction(self)
            action.setShortcut(QKeySequence(key))
            action.setShortcutContext(Qt.WidgetWithChildrenShortcut)
            action.triggered.connect(callback)
            self.addAction(action)

    def set_density(self, density: str) -> None:
        """Apply a row-density profile to the table.

        compact is useful for accounting/reporting grids; comfortable is the
        default ERP mode; touch is used for restaurant/POS screens.
        """
        density = (density or 'comfortable').strip().lower()
        sizes = {'compact': 28, 'comfortable': 34, 'touch': 44}
        if density not in sizes:
            density = 'comfortable'
        self._density = density
        self.verticalHeader().setDefaultSectionSize(sizes[density])
        self.setProperty('density', density)
        self._preferences.save_value(self._layout_key(), 'density', density)
        self.viewport().update()

    def restore_density(self) -> None:
        stored = self._preferences.load_value(self._layout_key(), 'density', 'comfortable')
        self.set_density(str(stored or 'comfortable'))

    def visible_columns(self) -> list:
        model = self.model()
        if not model:
            return []
        return [col for col in range(model.columnCount()) if not self.isColumnHidden(col)]

    def current_source_row(self):
        index = self.currentIndex()
        if not index.isValid():
            return None
        if self.model() is self._proxy_model:
            index = self._proxy_model.mapToSource(index)
        return index.row()

    def setModel(self, model):  # type: ignore[override]
        self._source_model = model
        # Preserve any active local filters after screen refreshes.
        if self._local_filter_text or self._column_filters:
            self._proxy_model.setSourceModel(model)
            super().setModel(self._proxy_model)
            self._proxy_model.set_search_text(self._local_filter_text)
            self._proxy_model.set_column_filters(self._column_filters)
        else:
            super().setModel(model)
        self.apply_enterprise_defaults()
        self.restore_density()
        QTimer.singleShot(0, self.fit_columns_to_view)
        try:
            self.schedule_initial_entry_focus(start_edit=False)
        except Exception:
            pass

    def apply_enterprise_defaults(self) -> None:
        # Phase389: SmartTableView is a list/action table by default.
        # Editable line grids opt into StandardTableKeyboardMixin explicitly;
        # list tables must use row-selection so edit/delete/print buttons can resolve
        # the selected business record even after visual/runtime polish passes.
        try:
            if not getattr(self, "_standard_keyboard_active", False):
                self.setSelectionBehavior(self.SelectRows)
                self.setSelectionMode(self.ExtendedSelection)
        except Exception:
            pass
        header = self.horizontalHeader()
        header.setSectionsMovable(True)
        header.setSectionsClickable(True)
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(self._minimum_interactive_width)
        header.setDefaultSectionSize(132)
        for col in range(self.model().columnCount() if self.model() else 0):
            header.setSectionResizeMode(col, QHeaderView.Interactive)

    def set_responsive_columns(self, enabled: bool = True) -> None:
        self._auto_fit_columns = bool(enabled)
        if enabled:
            self.fit_columns_to_view()

    def fit_columns_to_view(self) -> None:
        model = self.model()
        if not model or not self._auto_fit_columns:
            return
        visible = [col for col in range(model.columnCount()) if not self.isColumnHidden(col)]
        if not visible:
            return
        header = self.horizontalHeader()
        viewport_width = max(320, self.viewport().width())
        fixed_width = 0
        stretch_cols = []
        for col in visible:
            header_text = str(model.headerData(col, Qt.Horizontal, Qt.DisplayRole) or '')
            if any(key in header_text.lower() for key in ('id', '#', 'no', 'رقم')) or len(header_text) <= 3:
                width = max(self._minimum_interactive_width, min(96, header.sectionSize(col) or 84))
                self.setColumnWidth(col, width)
                fixed_width += width
            else:
                stretch_cols.append(col)
        if not stretch_cols:
            return
        available = max(self._minimum_interactive_width * len(stretch_cols), viewport_width - fixed_width - 24)
        per_col = max(self._minimum_interactive_width, int(available / len(stretch_cols)))
        for col in stretch_cols:
            self.setColumnWidth(col, per_col)

    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        if self._auto_fit_columns:
            QTimer.singleShot(0, self.fit_columns_to_view)

    def save_layout(self):  # type: ignore[override]
        super().save_layout()

    def restore_layout(self):  # type: ignore[override]
        super().restore_layout()
        self.restore_filter_state()

    def source_model(self):
        return self._source_model

    def _activate_proxy(self) -> None:
        if self._source_model is None:
            return
        if self.model() is not self._proxy_model:
            self._proxy_model.setSourceModel(self._source_model)
            super().setModel(self._proxy_model)

    def set_local_filter(self, text: str) -> None:
        self._local_filter_text = text or ""
        if self._source_model is None:
            return
        self._activate_proxy()
        self._proxy_model.set_search_text(self._local_filter_text)

    def set_column_filters(self, filters: Dict[int, str]) -> None:
        self._column_filters = {int(k): str(v) for k, v in (filters or {}).items() if str(v).strip()}
        if self._source_model is None:
            return
        self._activate_proxy()
        self._proxy_model.set_column_filters(self._column_filters)
        self.save_filter_state()

    def column_filters(self) -> Dict[int, str]:
        return dict(self._column_filters)

    def clear_filters(self) -> None:
        self._local_filter_text = ""
        self._column_filters = {}
        self._proxy_model.set_search_text("")
        self._proxy_model.set_column_filters({})
        if self._source_model is not None and self.model() is self._proxy_model:
            super().setModel(self._source_model)
        self.save_filter_state()

    def save_filter_state(self) -> None:
        self._preferences.save_value(self._layout_key(), "column_filters", self._column_filters)

    def restore_filter_state(self) -> None:
        stored = self._preferences.load_value(self._layout_key(), "column_filters", {}) or {}
        if isinstance(stored, dict):
            try:
                self._column_filters = {int(k): str(v) for k, v in stored.items() if str(v).strip()}
            except Exception:
                self._column_filters = {}

    def selected_source_rows(self):
        """Return selected source rows for row-action buttons.

        Phase389 keeps management/list tables row-selecting, but this method is
        deliberately tolerant: if an older view state or a proxy/filter leaves
        only cell indexes selected, edit/delete/print still resolves the row.
        """
        sm = self.selectionModel() if self.selectionModel() else None
        selection = sm.selectedRows() if sm else []
        if not selection and sm:
            try:
                selection = sm.selectedIndexes()
            except Exception:
                selection = []
        if not selection:
            try:
                idx = self.currentIndex()
                selection = [idx] if idx is not None and idx.isValid() else []
            except Exception:
                selection = []
        rows = []
        seen = set()
        for index in selection:
            if not index.isValid():
                continue
            if self.model() is self._proxy_model:
                index = self._proxy_model.mapToSource(index)
            row = index.row()
            if row not in seen:
                seen.add(row)
                rows.append(row)
        return rows

    def show_column_chooser(self) -> None:
        if getattr(self, "_column_contract", None) is not None and self.show_contract_column_customizer():
            return
        dialog = ColumnChooserDialog(self)
        dialog.exec_()
        self.save_layout()

    def show_filter_builder(self) -> None:
        dialog = FilterBuilderDialog(self)
        dialog.exec_()

    def save_view_preset(self, name: Optional[str] = None) -> None:
        name = (name or "").strip()
        if not name:
            name, ok = QInputDialog.getText(self, translate("save_view") if translate("save_view") != "save_view" else "Save view", translate("view_name") if translate("view_name") != "view_name" else "View name")
            if not ok or not name.strip():
                return
            name = name.strip()
        self.save_layout()
        self._preferences.save_named_view(
            self._layout_key(),
            name,
            self.horizontalHeader().saveState(),
            self._column_filters,
            bool(self._auto_fit_columns),
        )

    def apply_view_preset(self, name: str) -> None:
        preset = self._preferences.load_named_view(self._layout_key(), name)
        if not preset:
            return
        state = preset.get("header_state")
        if state:
            self.horizontalHeader().restoreState(state)
        self.set_responsive_columns(bool(preset.get("responsive", self._auto_fit_columns)))
        self.set_column_filters(preset.get("filters", {}) or {})

    def view_preset_names(self) -> list:
        return self._preferences.named_view_names(self._layout_key())

    def set_column_visible(self, column, visible):  # type: ignore[override]
        if not visible and self.model():
            visible_count = sum(1 for c in range(self.model().columnCount()) if not self.isColumnHidden(c))
            if visible_count <= 1:
                return
        super().set_column_visible(column, visible)
        if self._auto_fit_columns:
            QTimer.singleShot(0, self.fit_columns_to_view)

    def export_to_pdf(self) -> None:
        # Phase 235: legacy API name uses unified print, not PDF export.
        self.print_table('direct')

    def print_preview(self) -> None:
        self.print_table('preview')

    def set_layout_profile(self, profile_name: str) -> None:
        if profile_name:
            self.setProperty('layout_profile', profile_name)
            self.save_layout()

    def _show_menu(self, pos):  # type: ignore[override]
        menu = QMenu()
        copy_act = QAction(translate("copy"), self)
        copy_act.triggered.connect(self.copy_selection)
        menu.addAction(copy_act)
        menu.addSeparator()

        export_excel = QAction(translate("excel"), self)
        export_excel.triggered.connect(self.export_to_excel)
        menu.addAction(export_excel)
        print_act = QAction(translate("print"), self)
        print_act.triggered.connect(self.print_table)
        menu.addAction(print_act)
        menu.addSeparator()

        filter_act = QAction(translate("advanced_filters") if translate("advanced_filters") != "advanced_filters" else "Advanced filters", self)
        filter_act.triggered.connect(self.show_filter_builder)
        menu.addAction(filter_act)
        clear_filters = QAction(translate("clear_filters") if translate("clear_filters") != "clear_filters" else "Clear filters", self)
        clear_filters.triggered.connect(self.clear_filters)
        menu.addAction(clear_filters)

        fit_act = QAction(translate("fit_columns") if translate("fit_columns") != "fit_columns" else "Fit columns", self)
        fit_act.triggered.connect(self.fit_columns_to_view)
        menu.addAction(fit_act)

        responsive_act = QAction(translate("responsive_columns") if translate("responsive_columns") != "responsive_columns" else "Responsive columns", self)
        responsive_act.setCheckable(True)
        responsive_act.setChecked(self._auto_fit_columns)
        responsive_act.toggled.connect(self.set_responsive_columns)
        menu.addAction(responsive_act)

        column_chooser = QAction(translate("columns"), self)
        column_chooser.triggered.connect(self.show_column_chooser)
        menu.addAction(column_chooser)

        reset_columns = QAction(translate("reset_columns"), self)
        reset_columns.triggered.connect(self.reset_layout)
        menu.addAction(reset_columns)

        save_view = QAction(translate("save_view") if translate("save_view") != "save_view" else "Save view", self)
        save_view.triggered.connect(lambda: self.save_view_preset())
        menu.addAction(save_view)
        presets = self.view_preset_names()
        if presets:
            preset_menu = menu.addMenu(translate("view_presets") if translate("view_presets") != "view_presets" else "View presets")
            for name in presets:
                preset_menu.addAction(name, lambda n=name: self.apply_view_preset(n))

        density_menu = menu.addMenu(translate("row_density") if translate("row_density") != "row_density" else "Row density")
        for density_name, label in (("compact", "Compact"), ("comfortable", "Comfortable"), ("touch", "Touch")):
            density_action = QAction(translate(f"density_{density_name}") if translate(f"density_{density_name}") != f"density_{density_name}" else label, self)
            density_action.setCheckable(True)
            density_action.setChecked(getattr(self, "_density", "comfortable") == density_name)
            density_action.triggered.connect(lambda _checked=False, d=density_name: self.set_density(d))
            density_menu.addAction(density_action)

        # Phase 235: no PDF action in table context menus.
        menu.exec(self.viewport().mapToGlobal(pos))
