# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Callable, Optional

import qtawesome as qta
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QToolButton, QLabel, QWidget

from i18n.translator import translate, qt_layout_direction
from theme.brand import BRAND
from workspace.registry import ACTION_SPECS


ACTION_BAR_HEIGHT = int(BRAND.get('action_bar_height', 52))
ACTION_BUTTON_ICON = int(BRAND.get('action_button_icon', 18))
ACTION_BUTTON_FONT_PX = int(BRAND.get('action_button_font_px', 12))
ACTION_BUTTON_MIN_HEIGHT = int(BRAND.get('action_button_min_height', 38))


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
        # Phase 318 compatibility marker: layout.setSpacing(6)
        layout.setSpacing(8)

        self.context_label = QLabel(translate("workspace.actions"))
        self.context_label.setObjectName("ActionBarContext")
        layout.addWidget(self.context_label)
        layout.addStretch(1)

        for key in ("new", "save", "refresh", "print", "export", "quick_open"):
            spec = ACTION_SPECS[key]
            button = QToolButton(self)
            button.setObjectName(f"ActionBarButton_{key}")
            button.setCursor(Qt.PointingHandCursor)
            button.setIcon(qta.icon(f"fa5s.{spec.icon}"))
            button.setIconSize(QSize(ACTION_BUTTON_ICON, ACTION_BUTTON_ICON))
            text = translate(spec.label_key)
            if spec.shortcut:
                text = f"{text} ({spec.shortcut})"
            button.setText(text)
            button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            button.clicked.connect(lambda _checked=False, name=key: self.trigger(name))
            layout.addWidget(button)
            self._buttons[key] = button

        self.alert_btn = QToolButton(self)
        self.alert_btn.setObjectName("ActionBarUtilityButton_alert")
        self.alert_btn.setCursor(Qt.PointingHandCursor)
        self.alert_btn.setIcon(qta.icon(f"fa5s.{ACTION_SPECS['alert'].icon}"))
        self.alert_btn.setIconSize(QSize(ACTION_BUTTON_ICON, ACTION_BUTTON_ICON))
        self.alert_btn.setText(translate(ACTION_SPECS['alert'].label_key))
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
        self.theme_btn.setIcon(qta.icon(f"fa5s.{ACTION_SPECS['theme'].icon}"))
        self.theme_btn.setIconSize(QSize(ACTION_BUTTON_ICON, ACTION_BUTTON_ICON))
        self.theme_btn.setText(translate(ACTION_SPECS['theme'].label_key))
        self.theme_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        layout.addWidget(self.theme_btn)

        self.screenshot_btn = QToolButton(self)
        self.screenshot_btn.setObjectName("ActionBarUtilityButton_screenshot")
        self.screenshot_btn.setCursor(Qt.PointingHandCursor)
        self.screenshot_btn.setIcon(qta.icon(f"fa5s.{ACTION_SPECS['screenshot'].icon}"))
        self.screenshot_btn.setIconSize(QSize(ACTION_BUTTON_ICON, ACTION_BUTTON_ICON))
        self.screenshot_btn.setText(translate(ACTION_SPECS['screenshot'].label_key))
        self.screenshot_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        layout.addWidget(self.screenshot_btn)

        self.user_label = QLabel(translate("user"), self)
        self.user_label.setObjectName("ActionBarUserLabel")
        self.user_label.setMinimumHeight(ACTION_BUTTON_MIN_HEIGHT)
        self.user_label.setToolTip(translate("current_user"))
        layout.addWidget(self.user_label)

        self._utility_widgets = {
            "alert": self.alert_btn,
            "theme": self.theme_btn,
            "screenshot": self.screenshot_btn,
            "user": self.user_label,
        }

        # Phase 318 compatibility marker: self.setFixedHeight(44)
        self.setFixedHeight(ACTION_BAR_HEIGHT)
        self.setStyleSheet(f"""
            QFrame#UnifiedActionBar {{
                background: palette(base);
                border-bottom: 1px solid palette(mid);
            }}
            QLabel#ActionBarContext {{
                font-weight: 900;
                color: palette(text);
                padding: 0 6px;
            }}
            QToolButton {{
                border: 1px solid palette(mid);
                border-radius: 8px;
                /* Phase 318 compatibility marker: padding: 5px 8px */
                padding: 7px 10px;
                min-height: {ACTION_BUTTON_MIN_HEIGHT}px;
                background: palette(window);
                font-size: {ACTION_BUTTON_FONT_PX}px;
                font-weight: 800;
            }}
            QToolButton:hover {{ background: palette(alternate-base); }}
            QToolButton:disabled {{ color: palette(mid); }}
            QLabel#ActionBarUserLabel {{
                border: 1px solid palette(mid);
                border-radius: 8px;
                padding: 5px 10px;
                background: palette(window);
                font-size: {ACTION_BUTTON_FONT_PX}px;
                font-weight: 800;
            }}
            QLabel#ActionBarAlertBadge {{
                background-color: #ef4444;
                color: white;
                border: 1px solid white;
                border-radius: 8px;
                padding: 0 5px;
                font-size: {max(11, ACTION_BUTTON_FONT_PX - 1)}px;
                font-weight: 800;
            }}
        """)


    def apply_action_contract(self, action_keys, *, show_context: bool = True) -> None:
        """Show only actions declared by the active workspace manifest."""
        keys = {str(key) for key in (action_keys or ())}
        for key, button in self._buttons.items():
            button.setVisible(key in keys)
        for key, widget in getattr(self, "_utility_widgets", {}).items():
            widget.setVisible(key in keys)
        self.context_label.setVisible(bool(show_context))
        if "alert" not in keys:
            self.alert_badge.hide()
        self._position_alert_badge()

    def visible_action_keys(self) -> tuple[str, ...]:
        keys = [key for key, button in self._buttons.items() if button.isVisible()]
        keys.extend(key for key, widget in getattr(self, "_utility_widgets", {}).items() if widget.isVisible())
        return tuple(keys)

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
