# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtCore import QDate, Qt, pyqtSignal
from PyQt5.QtWidgets import QComboBox, QDateEdit, QGridLayout, QLabel, QLineEdit, QSizePolicy, QWidget

from i18n import qt_layout_direction, translate as tr


def _field_label(text: str, parent: QWidget) -> QLabel:
    label = QLabel(text if str(text).endswith(':') else f"{text}:", parent)
    label.setObjectName('FieldLabel')
    label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return label


class VoucherHeaderPanel(QWidget):
    """Voucher identity and descriptive fields used by VoucherEditorTab.

    Phase 267: the voucher document shell now uses a compact grid instead of a
    long single-column form layout.  This prevents the add-voucher screen from stacking every
    field under the previous one on wide screens while preserving the existing
    payload/load API used by VoucherEditorTab.
    """

    changed = pyqtSignal()

    def __init__(self, parent=None, voucher=None, voucher_type: str = 'receipt') -> None:
        super().__init__(parent)
        self.setObjectName('VoucherHeaderPanel')
        self.setLayoutDirection(qt_layout_direction())
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(8)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 0)
        layout.setColumnStretch(3, 1)

        self.type_combo = QComboBox()
        self.type_combo.setObjectName('voucher_type_combo')
        self.type_combo.addItem(tr('receipt'), 'receipt')
        self.type_combo.addItem(tr('payment'), 'payment')
        self.type_combo.addItem(tr('expense'), 'expense')

        self.date_edit = QDateEdit()
        self.date_edit.setObjectName('voucher_date_edit')
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())

        self.reference_edit = QLineEdit()
        self.reference_edit.setObjectName('voucher_reference_edit')
        self.reference_edit.setPlaceholderText(tr('reference_label'))

        self.description_edit = QLineEdit()
        self.description_edit.setObjectName('voucher_description_edit')
        self.description_edit.setPlaceholderText(tr('description_label'))

        for widget in (self.type_combo, self.date_edit, self.reference_edit, self.description_edit):
            widget.setMinimumHeight(30)
            widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._add_pair(layout, 0, 0, tr('type'), self.type_combo)
        self._add_pair(layout, 0, 2, tr('date_label'), self.date_edit)
        self._add_pair(layout, 1, 0, tr('reference_label'), self.reference_edit)
        self._add_pair(layout, 1, 2, tr('description_label'), self.description_edit)

        self.type_combo.currentIndexChanged.connect(lambda *_: self.changed.emit())
        self.date_edit.dateChanged.connect(lambda *_: self.changed.emit())
        self.description_edit.textChanged.connect(lambda *_: self.changed.emit())
        self.reference_edit.textChanged.connect(lambda *_: self.changed.emit())

        self.set_type(voucher.get('type') if isinstance(voucher, dict) else voucher_type)
        if isinstance(voucher, dict):
            self.load(voucher)

    def _add_pair(self, layout: QGridLayout, row: int, col: int, label_text: str, widget: QWidget) -> None:
        label = _field_label(label_text, self)
        layout.addWidget(label, row, col)
        layout.addWidget(widget, row, col + 1)

    def set_type(self, voucher_type: str) -> None:
        idx = self.type_combo.findData(voucher_type or 'receipt')
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)

    def voucher_type(self) -> str:
        return self.type_combo.currentData() or 'expense'

    def load(self, voucher: dict) -> None:
        self.set_type(voucher.get('type') or 'receipt')
        if voucher.get('date'):
            self.date_edit.setDate(QDate.fromString(str(voucher.get('date')), 'yyyy-MM-dd'))
        self.description_edit.setText(voucher.get('description') or '')
        self.reference_edit.setText(voucher.get('reference') or '')

    def payload(self) -> dict:
        return {
            'type': self.voucher_type(),
            'date': self.date_edit.date().toString('yyyy-MM-dd'),
            'description': self.description_edit.text().strip(),
            'reference': self.reference_edit.text().strip(),
        }
