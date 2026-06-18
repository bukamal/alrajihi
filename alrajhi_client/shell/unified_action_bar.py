# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Callable, Optional

import qtawesome as qta
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QToolButton, QLabel, QWidget

from i18n.translator import translate, qt_layout_direction


class UnifiedActionBar(QFrame):
    """Shared workspace command strip for high-frequency tab actions.

    The bar intentionally delegates to MainWindow command methods. Printing is
    routed through the existing tab command contract (`workspace_print`,
    `print_current`, `print_report`, etc.) so table/report/invoice printing
    remains centralized in `printing.printing_service`.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("UnifiedActionBar")
        self.setLayoutDirection(qt_layout_direction())
        self._callbacks = {}
        self._buttons = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        self.context_label = QLabel(translate("workspace.actions"))
        self.context_label.setObjectName("ActionBarContext")
        layout.addWidget(self.context_label)
        layout.addStretch(1)

        for key, icon, label_key, shortcut in [
            ("new", "fa5s.plus", "new", "Ctrl+N"),
            ("save", "fa5s.save", "save", "Ctrl+S"),
            ("refresh", "fa5s.sync-alt", "refresh_now", "F5"),
            ("print", "fa5s.print", "print", "Ctrl+P"),
            ("export", "fa5s.file-export", "export", ""),
            ("quick_open", "fa5s.search", "workspace.quick_open", "Ctrl+K"),
        ]:
            button = QToolButton(self)
            button.setObjectName(f"ActionBarButton_{key}")
            button.setCursor(Qt.PointingHandCursor)
            button.setIcon(qta.icon(icon))
            button.setIconSize(QSize(16, 16))
            text = translate(label_key)
            if shortcut:
                text = f"{text} ({shortcut})"
            button.setText(text)
            button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            button.clicked.connect(lambda _checked=False, name=key: self.trigger(name))
            layout.addWidget(button)
            self._buttons[key] = button

        self.setStyleSheet("""
            QFrame#UnifiedActionBar {
                background: palette(base);
                border-bottom: 1px solid palette(mid);
            }
            QLabel#ActionBarContext {
                font-weight: 900;
                color: palette(text);
                padding: 0 6px;
            }
            QToolButton {
                border: 1px solid palette(mid);
                border-radius: 9px;
                padding: 6px 10px;
                background: palette(window);
                font-weight: 700;
            }
            QToolButton:hover { background: palette(alternate-base); }
            QToolButton:disabled { color: palette(mid); }
        """)

    def bind(self, action: str, callback: Callable[[], None]) -> None:
        self._callbacks[action] = callback

    def trigger(self, action: str) -> None:
        callback = self._callbacks.get(action)
        if callback:
            callback()

    def set_context(self, title: str, dirty: bool = False) -> None:
        mark = " *" if dirty else ""
        self.context_label.setText(f"{title}{mark}" if title else translate("workspace.actions"))

    def set_action_enabled(self, action: str, enabled: bool) -> None:
        button = self._buttons.get(action)
        if button is not None:
            button.setEnabled(bool(enabled))
