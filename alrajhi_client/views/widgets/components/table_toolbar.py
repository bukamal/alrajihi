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

        self.columns_btn = QPushButton(translate("columns"))
        self.columns_btn.clicked.connect(self._show_columns_menu)
        layout.addWidget(self.columns_btn)

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
        model = self._table.model()
        menu = QMenu(self)
        for col in range(model.columnCount()):
            header = model.headerData(col, Qt.Horizontal, Qt.DisplayRole) or translate("column_number", number=col + 1)
            action = menu.addAction(str(header))
            action.setCheckable(True)
            action.setChecked(not self._table.isColumnHidden(col))
            action.toggled.connect(lambda checked, c=col: self._table.set_column_visible(c, checked))
        menu.addSeparator()
        reset_action = menu.addAction(translate("reset_columns"))
        reset_action.triggered.connect(self.resetColumnsRequested.emit)
        menu.exec_(self.columns_btn.mapToGlobal(self.columns_btn.rect().bottomLeft()))
