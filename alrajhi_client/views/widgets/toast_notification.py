# -*- coding: utf-8 -*-
"""Centralized non-blocking toast notifications for the application.

Phase 96: all transient save/server/status messages are anchored in one
professional location, stacked consistently instead of appearing wherever the
source widget happens to be located.
"""
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import QLabel, QFrame, QVBoxLayout, QApplication


class ToastNotification(QFrame):
    COLORS = {
        'success': ('#ecfdf5', '#047857', '#10b981'),
        'info': ('#eff6ff', '#1d4ed8', '#3b82f6'),
        'warning': ('#fffbeb', '#b45309', '#f59e0b'),
        'error': ('#fef2f2', '#b91c1c', '#ef4444'),
    }

    MARGIN = 26
    GAP = 10
    MAX_ACTIVE = 5

    def __init__(self, message, msg_type='info', parent=None, duration=2600):
        # Prefer the application main window so every toast uses the same anchor.
        super().__init__(self._main_window(parent))
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
                border-radius: 12px;
            }}
            QLabel {{
                color: {fg};
                font-size: 13px;
                font-weight: 700;
                padding: 9px 14px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        label = QLabel(self.message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label)
        self.setMinimumWidth(360)
        self.setMaximumWidth(560)
        self.adjustSize()

    @staticmethod
    def _main_window(parent=None):
        app = QApplication.instance()
        if app:
            for w in app.topLevelWidgets():
                if w.isVisible() and w.metaObject().className() == 'MainWindow':
                    return w
            active = QApplication.activeWindow()
            if active and active.isVisible():
                return active
        return parent

    def _target_parent_geometry(self):
        parent = self.parent()
        if parent and parent.isVisible():
            return parent.frameGeometry()
        screen = QApplication.primaryScreen()
        return screen.availableGeometry() if screen else None

    @classmethod
    def _active_toasts(cls):
        app = QApplication.instance()
        if app is None:
            return []
        refs = [t for t in getattr(app, '_toast_refs', []) if t is not None and not t.isHidden()]
        app._toast_refs = refs[-cls.MAX_ACTIVE:]
        return app._toast_refs

    def _register(self):
        app = QApplication.instance()
        if app is None:
            return
        refs = self._active_toasts()
        refs.append(self)
        app._toast_refs = refs[-self.MAX_ACTIVE:]

    @classmethod
    def reposition_all(cls):
        for idx, toast in enumerate(cls._active_toasts()):
            toast._place(idx)

    def _place(self, index=0):
        geom = self._target_parent_geometry()
        if not geom:
            return
        self.adjustSize()
        # Fixed professional anchor: top-center of the application window.
        x = geom.x() + max(0, (geom.width() - self.width()) // 2)
        y = geom.y() + self.MARGIN + index * (self.height() + self.GAP)
        self.move(max(0, x), max(0, y))

    def show_toast(self):
        self._register()
        self.reposition_all()
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self._fade_in = QPropertyAnimation(self, b'windowOpacity', self)
        self._fade_in.setDuration(160)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(0.97)
        self._fade_in.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_in.start()
        QTimer.singleShot(self.duration, self._fade_out)

    def _fade_out(self):
        self._fade = QPropertyAnimation(self, b'windowOpacity', self)
        self._fade.setDuration(260)
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(0.0)
        self._fade.setEasingCurve(QEasingCurve.InCubic)
        self._fade.finished.connect(self._close_and_reflow)
        self._fade.start()

    def _close_and_reflow(self):
        self.hide()
        self.deleteLater()
        QTimer.singleShot(0, self.reposition_all)
