# -*- coding: utf-8 -*-
"""Dialog for professional HTML table printing options.

Allows users to choose columns and basic report metadata before opening the
browser/HTML output. It is intentionally independent from the normal print path.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QDialogButtonBox, QCheckBox, QComboBox, QPushButton
)
from PyQt5.QtCore import Qt

try:
    from i18n.translator import translate_text
except Exception:
    def translate_text(x): return x


class HtmlPrintOptionsDialog(QDialog):
    def __init__(self, columns, default_title='تقرير جدول', parent=None):
        super().__init__(parent)
        self.setWindowTitle(translate_text('تخصيص طباعة HTML'))
        self.resize(520, 620)
        self.setLayoutDirection(Qt.RightToLeft)
        self._columns = list(columns or [])
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel('🖨️ ' + translate_text('تخصيص طباعة HTML'))
        title.setObjectName('sectionTitle')
        layout.addWidget(title)

        self.title_edit = QLineEdit(default_title or translate_text('تقرير جدول'))
        self.title_edit.setPlaceholderText(translate_text('عنوان التقرير'))
        layout.addWidget(QLabel(translate_text('عنوان التقرير') + ':'))
        layout.addWidget(self.title_edit)

        self.subtitle_edit = QLineEdit()
        self.subtitle_edit.setPlaceholderText(translate_text('وصف اختياري يظهر تحت العنوان'))
        layout.addWidget(QLabel(translate_text('وصف التقرير') + ':'))
        layout.addWidget(self.subtitle_edit)

        row = QHBoxLayout()
        self.paper_combo = QComboBox()
        self.paper_combo.addItem('A4', 'a4')
        self.paper_combo.addItem('Thermal 80mm', 'thermal80')
        self.paper_combo.addItem('Thermal 58mm', 'thermal58')
        row.addWidget(QLabel(translate_text('القالب') + ':'))
        row.addWidget(self.paper_combo)
        self.open_browser_check = QCheckBox(translate_text('فتح في المتصفح بعد الإنشاء'))
        self.open_browser_check.setChecked(True)
        row.addWidget(self.open_browser_check)
        layout.addLayout(row)

        layout.addWidget(QLabel(translate_text('اختر الأعمدة قبل فتح المتصفح') + ':'))
        self.columns_list = QListWidget()
        for col, header, checked in self._columns:
            item = QListWidgetItem(str(header))
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            item.setData(Qt.UserRole, int(col))
            self.columns_list.addItem(item)
        layout.addWidget(self.columns_list, 1)

        btns = QHBoxLayout()
        select_all = QPushButton(translate_text('تحديد الكل'))
        clear_all = QPushButton(translate_text('إلغاء الكل'))
        select_all.clicked.connect(lambda: self._set_all(Qt.Checked))
        clear_all.clicked.connect(lambda: self._set_all(Qt.Unchecked))
        btns.addWidget(select_all)
        btns.addWidget(clear_all)
        btns.addStretch()
        layout.addLayout(btns)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(translate_text('إنشاء HTML'))
        self.buttons.button(QDialogButtonBox.Cancel).setText(translate_text('إلغاء'))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self.setStyleSheet('''
            QDialog { background: #f8fafc; }
            QLabel#sectionTitle { font-size: 18px; font-weight: 700; color: #0f172a; padding: 8px; }
            QLineEdit, QComboBox { min-height: 34px; padding: 6px 10px; border: 1px solid #cbd5e1; border-radius: 8px; background: white; }
            QListWidget { background: white; border: 1px solid #cbd5e1; border-radius: 10px; padding: 6px; }
            QPushButton { min-height: 34px; border-radius: 8px; padding: 6px 12px; }
        ''')

    def _set_all(self, state):
        for i in range(self.columns_list.count()):
            self.columns_list.item(i).setCheckState(state)

    def selected_columns(self):
        selected = []
        for i in range(self.columns_list.count()):
            item = self.columns_list.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(int(item.data(Qt.UserRole)))
        return selected

    def options(self):
        return {
            'title': self.title_edit.text().strip() or translate_text('تقرير جدول'),
            'subtitle': self.subtitle_edit.text().strip(),
            'paper': self.paper_combo.currentData() or 'a4',
            'open_browser': self.open_browser_check.isChecked(),
            'columns': self.selected_columns(),
        }
