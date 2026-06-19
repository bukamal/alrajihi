# -*- coding: utf-8 -*-
"""Reusable table toolbar for search, actions, and column preferences."""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLineEdit, QLabel, QMenu
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from i18n import translate


class TableToolbar(QWidget):
    searchChanged = pyqtSignal(str)
    addRequested = pyqtSignal()
    deleteRequested = pyqtSignal()
    editRequested = pyqtSignal()
    exportRequested = pyqtSignal()
    printRequested = pyqtSignal()
    refreshRequested = pyqtSignal()
    resetColumnsRequested = pyqtSignal()
    fitColumnsRequested = pyqtSignal()
    filtersRequested = pyqtSignal()
    saveViewRequested = pyqtSignal()

    def __init__(self, entity_name=None, search_placeholder=None, parent=None):
        super().__init__(parent)
        entity_name = entity_name or translate('item')
        search_placeholder = search_placeholder or translate('search_placeholder')
        self._search_delay_ms = 250
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._emit_search)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.add_btn = QPushButton(translate("add_entity", entity=entity_name))
        self.add_btn.setObjectName("primary")
        self.add_btn.clicked.connect(self.addRequested.emit)
        layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton(translate("edit"))
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self.editRequested.emit)
        layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton(translate("delete"))
        self.delete_btn.setObjectName("danger")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.deleteRequested.emit)
        layout.addWidget(self.delete_btn)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(search_placeholder)
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMinimumWidth(220)
        self.search_edit.textChanged.connect(lambda *_: self._search_timer.start(self._search_delay_ms))
        layout.addWidget(self.search_edit, 1)

        self.filter_btn = QPushButton(translate("filters") if translate("filters") != "filters" else "Filters")
        self.filter_btn.setToolTip(translate("advanced_filters_hint") if translate("advanced_filters_hint") != "advanced_filters_hint" else "Advanced table filters")
        self.filter_btn.clicked.connect(self._show_filters)
        layout.addWidget(self.filter_btn)

        self.columns_btn = QPushButton(translate("columns"))
        self.columns_btn.setToolTip(translate("column_chooser_hint") if translate("column_chooser_hint") != "column_chooser_hint" else "Show, hide, reorder, and save columns")
        self.columns_btn.clicked.connect(self._show_columns_menu)
        layout.addWidget(self.columns_btn)

        self.fit_btn = QPushButton(translate("fit_columns") if translate("fit_columns") != "fit_columns" else "Fit")
        self.fit_btn.clicked.connect(self._fit_columns)
        layout.addWidget(self.fit_btn)

        self.export_btn = QPushButton(translate("excel"))
        self.export_btn.clicked.connect(self.exportRequested.emit)
        layout.addWidget(self.export_btn)

        self.print_btn = QPushButton(translate("print"))
        self.print_btn.clicked.connect(self.printRequested.emit)
        layout.addWidget(self.print_btn)

        self.refresh_btn = QPushButton(translate("refresh"))
        self.refresh_btn.clicked.connect(self.refreshRequested.emit)
        layout.addWidget(self.refresh_btn)

        self.counter_label = QLabel(translate("records_count", count=0))
        self.counter_label.setObjectName("muted")
        self.counter_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.counter_label)

        self._table = None

    def set_table(self, table):
        self._table = table
        self._install_unified_print_menu()

    def _install_unified_print_menu(self):
        """Attach standard print modes to toolbar print button for page tables.

        This keeps toolbar print buttons outside dialogs on the same central
        printing_service path used by invoice/return/report dialogs. Screens
        with specialized documents may override the menu after set_table().
        """
        if not self._table or not hasattr(self._table, 'print_table'):
            return
        menu = QMenu(self.print_btn)
        menu.addAction(translate('preview_in_app'), lambda: self._table.print_table('preview'))
        menu.addAction(translate('open_html_browser'), lambda: self._table.print_table('browser'))
        menu.addSeparator()
        menu.addAction(translate('direct_print'), lambda: self._table.print_table('direct'))
        self.print_btn.setMenu(menu)

    def search_text(self):
        return self.search_edit.text()

    def set_counter(self, text):
        self.counter_label.setText(text)

    def set_delete_enabled(self, enabled):
        self.delete_btn.setEnabled(bool(enabled))

    def set_edit_enabled(self, enabled):
        if hasattr(self, 'edit_btn'):
            self.edit_btn.setEnabled(bool(enabled))

    def set_add_visible(self, visible):
        self.add_btn.setVisible(bool(visible))

    def set_delete_visible(self, visible):
        self.delete_btn.setVisible(bool(visible))

    def set_edit_visible(self, visible):
        if hasattr(self, 'edit_btn'):
            self.edit_btn.setVisible(bool(visible))

    def set_export_visible(self, visible):
        self.export_btn.setVisible(bool(visible))

    def set_print_visible(self, visible):
        self.print_btn.setVisible(bool(visible))

    def _emit_search(self):
        self.searchChanged.emit(self.search_edit.text())

    def _show_columns_menu(self):
        if not self._table or not self._table.model():
            return
        menu = QMenu(self)
        chooser_action = menu.addAction(translate("columns"))
        if hasattr(self._table, "show_column_chooser"):
            chooser_action.triggered.connect(self._table.show_column_chooser)
        fit_action = menu.addAction(translate("fit_columns") if translate("fit_columns") != "fit_columns" else "Fit columns")
        fit_action.triggered.connect(self._fit_columns)
        responsive_action = menu.addAction(translate("responsive_columns") if translate("responsive_columns") != "responsive_columns" else "Responsive columns")
        responsive_action.setCheckable(True)
        responsive_action.setChecked(bool(getattr(self._table, "_auto_fit_columns", False)))
        responsive_action.toggled.connect(lambda checked: getattr(self._table, "set_responsive_columns", lambda _c: None)(checked))
        menu.addSeparator()
        # Phase 235: no PDF action in table print menus.
        save_view_action = menu.addAction(translate("save_view") if translate("save_view") != "save_view" else "Save view")
        save_view_action.triggered.connect(self._save_view)
        if self._table and hasattr(self._table, "view_preset_names"):
            preset_names = self._table.view_preset_names()
            if preset_names:
                presets_menu = menu.addMenu(translate("view_presets") if translate("view_presets") != "view_presets" else "View presets")
                for name in preset_names:
                    presets_menu.addAction(name, lambda n=name: getattr(self._table, "apply_view_preset", lambda _n: None)(n))
        reset_action = menu.addAction(translate("reset_columns"))
        reset_action.triggered.connect(self.resetColumnsRequested.emit)
        menu.exec_(self.columns_btn.mapToGlobal(self.columns_btn.rect().bottomLeft()))

    def _fit_columns(self):
        self.fitColumnsRequested.emit()
        if self._table and hasattr(self._table, "fit_columns_to_view"):
            self._table.fit_columns_to_view()

    def _show_filters(self):
        self.filtersRequested.emit()
        if self._table and hasattr(self._table, "show_filter_builder"):
            self._table.show_filter_builder()

    def _save_view(self):
        self.saveViewRequested.emit()
        if self._table and hasattr(self._table, "save_view_preset"):
            self._table.save_view_preset()
