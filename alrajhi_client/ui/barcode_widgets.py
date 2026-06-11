# -*- coding: utf-8 -*-
"""Unified barcode input helpers.

Many USB barcode readers behave like keyboards and can append suffix keys
such as Enter, Tab or Escape.  Escape must never trigger dialog cancel,
cart reset, page navigation or exit confirmation while the focus is inside a
barcode field.  This module centralises that rule for all project windows.
"""

try:
    from PyQt5.QtCore import Qt, QEvent, QTimer, pyqtSignal
    from PyQt5.QtWidgets import QLineEdit, QApplication
except Exception:  # pragma: no cover - allows static import in limited envs
    Qt = QEvent = QTimer = pyqtSignal = QLineEdit = QApplication = None


class BarcodeLineEdit(QLineEdit):
    """QLineEdit tuned for continuous barcode scanning.

    - Swallows Escape produced by scanners.
    - Keeps focus ready for the next scan.
    - Marks itself as a barcode field so global Esc shortcuts can ignore it.
    """

    escapeIgnored = pyqtSignal()

    def __init__(self, parent=None, *, clear_on_escape=True, refocus_on_escape=True):
        super().__init__(parent)
        self._clear_on_escape = clear_on_escape
        self._refocus_on_escape = refocus_on_escape
        self.setProperty("barcodeField", True)
        self.setObjectName("barcodeInput")

    def keyPressEvent(self, event):
        if event is not None and event.key() == Qt.Key_Escape:
            if self._clear_on_escape:
                self.clear()
            if self._refocus_on_escape:
                QTimer.singleShot(0, self.setFocus)
            self.escapeIgnored.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def event(self, event):
        # Some platforms deliver scanner suffixes as ShortcutOverride before
        # keyPressEvent. Accepting it here prevents parent QShortcut handlers
        # from seeing Escape while this input owns the focus.
        if event is not None and event.type() == QEvent.ShortcutOverride and event.key() == Qt.Key_Escape:
            event.accept()
            return True
        return super().event(event)


def focused_widget_is_barcode():
    """Return True when the active focus widget is a barcode input field."""
    try:
        widget = QApplication.focusWidget()
        while widget is not None:
            if bool(widget.property("barcodeField")):
                return True
            widget = widget.parentWidget()
    except Exception:
        return False
    return False


def ignore_if_barcode_focus(action):
    """Wrap shortcut handlers so scanner Escape cannot trigger them."""
    def _wrapped(*args, **kwargs):
        if focused_widget_is_barcode():
            return None
        return action(*args, **kwargs)
    return _wrapped
