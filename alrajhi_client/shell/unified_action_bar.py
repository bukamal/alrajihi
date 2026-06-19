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

        self.alert_btn = QToolButton(self)
        self.alert_btn.setObjectName("ActionBarUtilityButton_alert")
        self.alert_btn.setCursor(Qt.PointingHandCursor)
        self.alert_btn.setIcon(qta.icon("fa5s.bell"))
        self.alert_btn.setIconSize(QSize(16, 16))
        self.alert_btn.setText(translate("alerts"))
        self.alert_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        layout.addWidget(self.alert_btn)

        self.alert_badge = QLabel("", self.alert_btn)
        self.alert_badge.setObjectName("ActionBarAlertBadge")
        self.alert_badge.setAlignment(Qt.AlignCenter)
        self.alert_badge.setFixedHeight(18)
        self.alert_badge.setMinimumWidth(18)
        self.alert_badge.hide()

        self.theme_btn = QToolButton(self)
        self.theme_btn.setObjectName("ActionBarUtilityButton_theme")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.setIcon(qta.icon("fa5s.adjust"))
        self.theme_btn.setIconSize(QSize(16, 16))
        self.theme_btn.setText(translate("toggle_theme"))
        self.theme_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        layout.addWidget(self.theme_btn)

        self.screenshot_btn = QToolButton(self)
        self.screenshot_btn.setObjectName("ActionBarUtilityButton_screenshot")
        self.screenshot_btn.setCursor(Qt.PointingHandCursor)
        self.screenshot_btn.setIcon(qta.icon("fa5s.camera"))
        self.screenshot_btn.setIconSize(QSize(16, 16))
        self.screenshot_btn.setText(translate("export_screenshot"))
        self.screenshot_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        layout.addWidget(self.screenshot_btn)

        self.user_label = QLabel(translate("user"), self)
        self.user_label.setObjectName("ActionBarUserLabel")
        self.user_label.setMinimumHeight(30)
        self.user_label.setToolTip(translate("current_user"))
        layout.addWidget(self.user_label)

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
            QLabel#ActionBarUserLabel {
                border: 1px solid palette(mid);
                border-radius: 9px;
                padding: 5px 10px;
                background: palette(window);
                font-weight: 800;
            }
            QLabel#ActionBarAlertBadge {
                background-color: #ef4444;
                color: white;
                border: 1px solid white;
                border-radius: 9px;
                padding: 0 5px;
                font-size: 10px;
                font-weight: 800;
            }
        """)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_alert_badge()

    def _position_alert_badge(self) -> None:
        try:
            self.alert_badge.adjustSize()
            w = max(18, self.alert_badge.width())
            self.alert_badge.setFixedWidth(w)
            self.alert_badge.move(self.alert_btn.width() - w - 3, 2)
        except Exception:
            pass

    def set_alert_badge(self, count: int) -> None:
        try:
            count = int(count or 0)
        except Exception:
            count = 0
        if count <= 0:
            self.alert_badge.hide()
            self.alert_btn.setToolTip(translate("alerts"))
            return
        text = "99+" if count > 99 else str(count)
        self.alert_badge.setText(text)
        self.alert_badge.show()
        self.alert_badge.raise_()
        self.alert_btn.setToolTip(f"{translate('alerts')} ({count})")
        self._position_alert_badge()

    def set_user(self, username: str, role: str = "") -> None:
        label = username or translate("user")
        display = f"👤 {label}"
        if role:
            display += f" · {role}"
        self.user_label.setText(display)
        self.user_label.setToolTip(display)

    def apply_styles(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)

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
