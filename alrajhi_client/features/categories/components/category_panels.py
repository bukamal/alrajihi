# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QCheckBox, QComboBox, QFormLayout, QFrame, QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout

from i18n import translate


class CategoryHeaderPanel(QFrame):
    saveRequested = pyqtSignal()

    def __init__(self, is_edit: bool, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName('DocumentHeaderCard')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        self.title_label = QLabel(translate('edit_category') if is_edit else translate('add_category'))
        self.title_label.setObjectName('DocumentTitle')
        layout.addWidget(self.title_label)
        self.subtitle_label = QLabel(translate('categories_hint'))
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)
        self.save_btn = QPushButton(translate('save'))
        self.save_btn.setObjectName('primary')
        self.save_btn.clicked.connect(self.saveRequested.emit)
        layout.addWidget(self.save_btn, 0, Qt.AlignRight)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_subtitle(self, text: str) -> None:
        self.subtitle_label.setText(text)


class CategoryPropertiesPanel(QFrame):
    changed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName('FormCard')
        form = QFormLayout(self)
        form.setLabelAlignment(Qt.AlignRight)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(translate('category_name'))
        self.parent_combo = QComboBox()
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(110)
        self.active_check = QCheckBox(translate('active'))
        self.active_check.setChecked(True)
        form.addRow(translate('name_label'), self.name_edit)
        form.addRow(translate('parent_category_label'), self.parent_combo)
        form.addRow(translate('description_label'), self.description_edit)
        form.addRow('', self.active_check)
        self.name_edit.textChanged.connect(lambda _text: self.changed.emit())
        self.description_edit.textChanged.connect(self.changed.emit)
        self.parent_combo.currentIndexChanged.connect(lambda _index: self.changed.emit())
        self.active_check.stateChanged.connect(lambda _state: self.changed.emit())

    def set_parent_categories(self, rows, current_category_id=None) -> None:
        self.parent_combo.blockSignals(True)
        self.parent_combo.clear()
        self.parent_combo.addItem(translate('no_parent'), None)
        for cat in rows:
            if current_category_id is not None and int(cat.get('id')) == int(current_category_id):
                continue
            self.parent_combo.addItem(cat.get('full_name') or cat.get('name', ''), cat.get('id'))
        self.parent_combo.blockSignals(False)

    def load_category(self, category: dict) -> None:
        self.name_edit.setText(category.get('name', ''))
        self.description_edit.setPlainText(category.get('description') or '')
        self.active_check.setChecked(int(category.get('is_active') or 0) == 1 and not category.get('deleted_at'))
        parent_id = category.get('parent_id')
        if parent_id is not None:
            idx = self.parent_combo.findData(parent_id)
            if idx >= 0:
                self.parent_combo.setCurrentIndex(idx)

    def payload(self) -> dict:
        return {
            'name': self.name_edit.text().strip(),
            'parent_id': self.parent_combo.currentData(),
            'description': self.description_edit.toPlainText().strip(),
            'is_active': 1 if self.active_check.isChecked() else 0,
            'color': '#64748B',
            'icon': 'folder',
        }

    def set_read_only(self, read_only: bool) -> None:
        self.name_edit.setReadOnly(read_only)
        self.description_edit.setReadOnly(read_only)
        self.parent_combo.setEnabled(not read_only)
        self.active_check.setEnabled(not read_only)

    def focus_name(self) -> None:
        self.name_edit.setFocus()
