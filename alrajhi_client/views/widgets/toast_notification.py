# -*- coding: utf-8 -*-
"""Non-blocking toast notifications for the application."""
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import QLabel, QFrame, QVBoxLayout, QApplication


class ToastNotification(QFrame):
    COLORS = {
        'success': ('#ecfdf5', '#047857', '#10b981'),
        'info': ('#eff6ff', '#1d4ed8', '#3b82f6'),
        'warning': ('#fffbeb', '#b45309', '#f59e0b'),
        'error': ('#fef2f2', '#b91c1c', '#ef4444'),
    }

    def __init__(self, message, msg_type='info', parent=None, duration=2600):
        super().__init__(parent)
        self.message = str(message or '')
        self.msg_type = msg_type if msg_type in self.COLORS else 'info'
        self.duration = duration
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setObjectName('ToastNotification')
        bg, fg, accent = self.COLORS[self.msg_type]
        self.setStyleSheet(f"""
            QFrame#ToastNotification {{
                background: {bg};
                border: 1px solid {accent};
                border-right: 5px solid {accent};
                border-radius: 10px;
            }}
            QLabel {{
                color: {fg};
                font-size: 13px;
                font-weight: 600;
                padding: 8px 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        label = QLabel(self.message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label)
        self.setMinimumWidth(320)
        self.setMaximumWidth(520)
        self.adjustSize()

    def _target_parent_geometry(self):
        parent = self.parent()
        if parent and parent.isVisible():
            return parent.frameGeometry()
        screen = QApplication.primaryScreen()
        return screen.availableGeometry() if screen else None

    def _place(self):
        geom = self._target_parent_geometry()
        if not geom:
            return
        self.adjustSize()
        x = geom.x() + geom.width() - self.width() - 28
        y = geom.y() + 28
        self.move(max(0, x), max(0, y))

    def show_toast(self):
        self._place()
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self._fade_in = QPropertyAnimation(self, b'windowOpacity', self)
        self._fade_in.setDuration(160)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(0.96)
        self._fade_in.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_in.start()
        QTimer.singleShot(self.duration, self._fade_out)

    def _fade_out(self):
        self._fade = QPropertyAnimation(self, b'windowOpacity', self)
        self._fade.setDuration(260)
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(0.0)
        self._fade.setEasingCurve(QEasingCurve.InCubic)
        self._fade.finished.connect(self.deleteLater)
        self._fade.start()
