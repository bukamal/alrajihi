# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QToolBar, QWidget

from i18n.translator import translate, qt_layout_direction
from theme.brand import BRAND, get_tokens
from core.services.settings_service import settings_service


@dataclass
class OperationalFullscreenSnapshot:
    """Visual shell state captured before entering operational fullscreen."""

    widget_visibility: Dict[QWidget, bool]
    tab_bar_visible: Optional[bool]
    was_maximized: bool
    was_fullscreen: bool


class OperationalFullscreenController:
    """Central owner for operational fullscreen mode.

    This controller intentionally belongs to MainWindow, not to POS or
    Restaurant pages.  It hides shell chrome from one place and restores the
    previous state exactly when leaving fullscreen.  Feature pages may expose a
    local button, but they must call MainWindow.toggle_operational_fullscreen()
    instead of using showFullScreen()/showNormal() directly.
    """

    PHASE = 429
    CHROME_WIDGET_ATTRS = (
        "menu_bar",
        "action_bar",
        "notification_center",
    )

    def __init__(self, main_window) -> None:
        self.main_window = main_window
        self._snapshot: Optional[OperationalFullscreenSnapshot] = None
        self._active = False
        self._exit_button = self._build_exit_button()
        self._exit_button.hide()

    def _build_exit_button(self) -> QPushButton:
        button = QPushButton(translate("exit_fullscreen"), self.main_window)
        button.setObjectName("OperationalFullscreenExitButton")
        button.setProperty("operationalFullscreen", True)
        button.setCursor(Qt.PointingHandCursor)
        button.setLayoutDirection(qt_layout_direction())
        button.clicked.connect(self.exit)
        button.setFixedHeight(int(BRAND.get("action_button_min_height", 38)) + 4)
        self._apply_exit_button_style(button)
        return button

    def _apply_exit_button_style(self, button: QPushButton) -> None:
        colors = get_tokens(settings_service.get_theme() or "light")
        button.setStyleSheet(f"""
            QPushButton#OperationalFullscreenExitButton {{
                background: {colors.get('basit_red', colors['danger'])};
                color: #FFFFFF;
                border: 2px solid {colors.get('basit_yellow', colors['warning'])};
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 950;
                font-size: 13px;
            }}
            QPushButton#OperationalFullscreenExitButton:hover {{
                background: {colors.get('basit_red_dark', colors.get('danger', '#991B1B'))};
            }}
        """)

    def _shell_chrome_widgets(self) -> Iterable[QWidget]:
        seen: set[int] = set()
        for attr in self.CHROME_WIDGET_ATTRS:
            widget = getattr(self.main_window, attr, None)
            if isinstance(widget, QWidget) and id(widget) not in seen:
                seen.add(id(widget))
                yield widget
        # Any real QToolBar added later must also disappear in operational mode.
        try:
            for toolbar in self.main_window.findChildren(QToolBar):
                if id(toolbar) not in seen:
                    seen.add(id(toolbar))
                    yield toolbar
        except Exception:
            return

    def is_active(self) -> bool:
        return bool(self._active)

    def enter(self) -> None:
        if self._active:
            return
        tab_bar_visible = None
        try:
            tab_bar_visible = bool(self.main_window.workspace.tabBar().isVisible())
        except Exception:
            pass
        widget_visibility = {widget: bool(widget.isVisible()) for widget in self._shell_chrome_widgets()}
        self._snapshot = OperationalFullscreenSnapshot(
            widget_visibility=widget_visibility,
            tab_bar_visible=tab_bar_visible,
            was_maximized=bool(self.main_window.isMaximized()),
            was_fullscreen=bool(self.main_window.isFullScreen()),
        )
        for widget in widget_visibility:
            try:
                widget.setVisible(False)
            except Exception:
                pass
        try:
            self.main_window.workspace.tabBar().setVisible(False)
        except Exception:
            pass
        self.main_window.showFullScreen()
        self._active = True
        self._show_exit_button()
        self._notify_pages(True)

    def exit(self) -> None:
        if not self._active:
            return
        snapshot = self._snapshot
        self._exit_button.hide()
        if snapshot is not None:
            for widget, visible in snapshot.widget_visibility.items():
                try:
                    widget.setVisible(bool(visible))
                except Exception:
                    pass
            if snapshot.tab_bar_visible is not None:
                try:
                    self.main_window.workspace.tabBar().setVisible(bool(snapshot.tab_bar_visible))
                except Exception:
                    pass
            if snapshot.was_fullscreen:
                self.main_window.showFullScreen()
            elif snapshot.was_maximized:
                self.main_window.showMaximized()
            else:
                self.main_window.showNormal()
        else:
            self.main_window.showNormal()
        self._active = False
        self._snapshot = None
        self._notify_pages(False)

    def toggle(self) -> None:
        if self._active:
            self.exit()
        else:
            self.enter()

    def _show_exit_button(self) -> None:
        self._exit_button.setText(translate("exit_fullscreen"))
        self._exit_button.adjustSize()
        width = max(self._exit_button.width(), 150)
        self._exit_button.setFixedWidth(width)
        margin = 16
        if qt_layout_direction() == Qt.RightToLeft:
            x = margin
        else:
            x = max(margin, self.main_window.width() - width - margin)
        self._exit_button.move(x, margin)
        self._exit_button.show()
        self._exit_button.raise_()

    def refresh_overlay_position(self) -> None:
        if self._active:
            self._show_exit_button()

    def _notify_pages(self, active: bool) -> None:
        """Let operational pages update local button labels without owning mode."""
        candidates = []
        try:
            candidates.extend(self.main_window.pages.values())
        except Exception:
            pass
        try:
            current = self.main_window._active_shell_page()
            if current is not None and current not in candidates:
                candidates.append(current)
        except Exception:
            pass
        for page in candidates:
            hook = getattr(page, "set_operational_fullscreen_active", None)
            if callable(hook):
                try:
                    hook(bool(active))
                except Exception:
                    pass
