# -*- coding: utf-8 -*-
"""Reusable form validation helpers for professional dialogs.

The goal is to keep field validation consistent across dialogs without moving
business rules away from services.  Validators only handle UI-level feedback:
required fields, positive numeric values, and displaying errors next to fields.
"""
from __future__ import annotations

from typing import Optional

from PyQt5.QtWidgets import QLabel, QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QWidget


def make_error_label(text: str = "") -> QLabel:
    label = QLabel(text)
    label.setObjectName("fieldError")
    label.setVisible(bool(text))
    label.setWordWrap(True)
    return label


class FormValidator:
    def __init__(self):
        self._first_invalid: Optional[QWidget] = None
        self._valid = True

    def reset(self):
        self._first_invalid = None
        self._valid = True

    @property
    def is_valid(self) -> bool:
        return self._valid

    def _set_invalid(self, widget: QWidget, label: QLabel, message: str):
        self._valid = False
        if self._first_invalid is None:
            self._first_invalid = widget
        if label is not None:
            label.setText(message)
            label.setVisible(True)
        self.mark_invalid(widget, True)

    @staticmethod
    def mark_invalid(widget: QWidget, invalid: bool):
        if widget is None:
            return
        widget.setProperty("invalid", bool(invalid))
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    @staticmethod
    def clear(label: QLabel, widget: QWidget = None):
        if label is not None:
            label.clear()
            label.setVisible(False)
        if widget is not None:
            FormValidator.mark_invalid(widget, False)

    def required(self, widget: QWidget, label: QLabel, field_name: str) -> bool:
        value = ""
        if isinstance(widget, QLineEdit):
            value = widget.text().strip()
        elif isinstance(widget, (QTextEdit, QPlainTextEdit)):
            value = widget.toPlainText().strip()
        else:
            value = str(getattr(widget, 'text', lambda: '')()).strip()
        if not value:
            self._set_invalid(widget, label, f"{field_name} مطلوب")
            return False
        self.clear(label, widget)
        return True

    def positive(self, widget: QWidget, label: QLabel, field_name: str, allow_zero: bool = False) -> bool:
        try:
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                value = widget.value()
            else:
                value = float(str(getattr(widget, 'text', lambda: '0')()).strip() or '0')
        except Exception:
            self._set_invalid(widget, label, f"{field_name} يجب أن يكون رقمًا صحيحًا")
            return False
        ok = value >= 0 if allow_zero else value > 0
        if not ok:
            self._set_invalid(widget, label, f"{field_name} يجب أن يكون {'صفرًا أو أكبر' if allow_zero else 'أكبر من صفر'}")
            return False
        self.clear(label, widget)
        return True

    def custom(self, condition: bool, widget: QWidget, label: QLabel, message: str) -> bool:
        if not condition:
            self._set_invalid(widget, label, message)
            return False
        self.clear(label, widget)
        return True

    def focus_first_invalid(self):
        if self._first_invalid is not None:
            try:
                self._first_invalid.setFocus()
            except Exception:
                pass
