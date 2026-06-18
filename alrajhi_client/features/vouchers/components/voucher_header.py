# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtCore import QDate, pyqtSignal
from PyQt5.QtWidgets import QComboBox, QDateEdit, QFormLayout, QLineEdit, QWidget

from i18n import translate as tr


class VoucherHeaderPanel(QWidget):
    """Voucher identity and descriptive fields used by VoucherEditorTab."""

    changed = pyqtSignal()

    def __init__(self, parent=None, voucher=None, voucher_type: str = 'receipt') -> None:
        super().__init__(parent)
        layout = QFormLayout(self)

        self.type_combo = QComboBox()
        self.type_combo.addItem(tr('receipt'), 'receipt')
        self.type_combo.addItem(tr('payment'), 'payment')
        self.type_combo.addItem(tr('expense'), 'expense')
        layout.addRow(tr('type') + ':', self.type_combo)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        layout.addRow(tr('date_label'), self.date_edit)

        self.description_edit = QLineEdit()
        layout.addRow(tr('description_label'), self.description_edit)

        self.reference_edit = QLineEdit()
        layout.addRow(tr('reference_label'), self.reference_edit)

        for widget in (self.type_combo, self.date_edit, self.description_edit, self.reference_edit):
            signal = getattr(widget, 'currentIndexChanged', None) or getattr(widget, 'dateChanged', None) or getattr(widget, 'textChanged', None)
            try:
                signal.connect(lambda *_: self.changed.emit())
            except Exception:
                pass

        self.set_type(voucher.get('type') if isinstance(voucher, dict) else voucher_type)
        if isinstance(voucher, dict):
            self.load(voucher)

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
