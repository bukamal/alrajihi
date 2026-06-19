# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QVBoxLayout, QListWidget, QListWidgetItem, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from views.centered_dialog import CenteredDialog
from i18n import translate

class ColumnCustomizerDialog(CenteredDialog):
    def __init__(self, parent, columns, visible_columns, table_name):
        super().__init__(parent)
        self.setWindowTitle(translate('phase233_column_customizer_title', table=table_name))
        self.resize(450, 550)
        self.columns = columns
        self.visible_columns = visible_columns.copy()
        self.setup_ui()

    def setup_ui(self):
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        for col_id, col_name in self.columns:
            item = QListWidgetItem(col_name)
            item.setData(Qt.UserRole, col_id)
            item.setCheckState(Qt.Checked if col_id in self.visible_columns else Qt.Unchecked)
            self.list_widget.addItem(item)
        self.content_layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton(translate('phase233_ui_028'))
        save_btn.setObjectName("primary")
        cancel_btn = QPushButton(translate('phase233_ui_020'))
        select_all_btn = QPushButton(translate('phase233_ui_029'))
        deselect_all_btn = QPushButton(translate('phase233_ui_030'))
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        self.content_layout.addLayout(btn_layout)

        select_all_btn.clicked.connect(self.select_all)
        deselect_all_btn.clicked.connect(self.deselect_all)
        save_btn.clicked.connect(self.save)
        cancel_btn.clicked.connect(self.reject)
        self.install_form_shortcuts(self.save)

    def select_all(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Checked)

    def deselect_all(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)

    def save(self):
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))
        self.visible_columns = selected
        self.accept()


