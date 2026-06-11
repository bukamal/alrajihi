# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt, QEvent, QObject
from .frameless_dialog import FramelessDialog
from PyQt5.QtWidgets import QMessageBox, QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QCheckBox
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
from utils import focus_first_input

class CenteredDialog(FramelessDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(500, 400)
        self._parent_move_filter = None
        self._dirty_tracking_enabled = False
        self._dirty = False
        self._standard_shortcuts = []
        if self.parent():
            self._install_parent_filter()
    
    def _install_parent_filter(self):
        if self._parent_move_filter is not None:
            return
        self._parent_move_filter = ParentMoveFilter(self)
        self.parent().installEventFilter(self._parent_move_filter)
    
    def showEvent(self, event):
        super().showEvent(event)
        if self.parent() and not self._parent_move_filter:
            self._install_parent_filter()
        self._center_on_main_window()
        focus_first_input(self)
    
    def _confirm_discard_changes(self) -> bool:
        if not getattr(self, '_dirty_tracking_enabled', False) or not getattr(self, '_dirty', False):
            return True
        reply = QMessageBox.question(
            self,
            'تغييرات غير محفوظة',
            'لديك تغييرات غير محفوظة. هل تريد الخروج دون حفظ؟',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return reply == QMessageBox.Yes

    def mark_dirty(self):
        if getattr(self, '_dirty_tracking_enabled', False):
            self._dirty = True

    def reset_dirty(self):
        self._dirty = False

    def watch_dirty_widgets(self, widgets, reset: bool = True):
        self._dirty_tracking_enabled = True
        for widget in widgets:
            if widget is None:
                continue
            try:
                if isinstance(widget, (QLineEdit, QTextEdit, QPlainTextEdit)):
                    widget.textChanged.connect(self.mark_dirty)
                elif isinstance(widget, QComboBox):
                    widget.currentIndexChanged.connect(self.mark_dirty)
                elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    widget.valueChanged.connect(self.mark_dirty)
                elif isinstance(widget, QDateEdit):
                    widget.dateChanged.connect(self.mark_dirty)
                elif isinstance(widget, QCheckBox):
                    widget.stateChanged.connect(self.mark_dirty)
            except Exception:
                pass
        if reset:
            self.reset_dirty()

    def install_form_shortcuts(self, save_handler=None, cancel_handler=None):
        if save_handler:
            for key in ('Ctrl+S', 'Ctrl+Return'):
                shortcut = QShortcut(QKeySequence(key), self)
                shortcut.activated.connect(save_handler)
                self._standard_shortcuts.append(shortcut)
        shortcut = QShortcut(QKeySequence('Esc'), self)
        shortcut.activated.connect(cancel_handler or self.reject)
        self._standard_shortcuts.append(shortcut)

    def reject(self):
        if self._confirm_discard_changes():
            super().reject()

    def accept(self):
        self.reset_dirty()
        super().accept()

    def closeEvent(self, event):
        if not self._confirm_discard_changes():
            event.ignore()
            return
        if self._parent_move_filter and self.parent():
            self.parent().removeEventFilter(self._parent_move_filter)
            self._parent_move_filter = None
        super().closeEvent(event)

class ParentMoveFilter(QObject):
    def __init__(self, dialog):
        super().__init__(dialog)
        self.dialog = dialog
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Move:
            try:
                if self.dialog and self.dialog.isVisible():
                    self.dialog._center_on_main_window()
            except RuntimeError:
                pass
        return super().eventFilter(obj, event)


