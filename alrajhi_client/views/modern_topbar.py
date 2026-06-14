# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFrame, QToolButton, QMenu, QLineEdit, QScrollArea, QSizePolicy
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon
import qtawesome as qta
from i18n.translator import translate, qt_layout_direction
from core.services.settings_service import settings_service

class TopBarButton(QPushButton):
    def __init__(self, text, icon_name, badge_count=0, parent=None, show_text=True):
        super().__init__(parent)
        self.original_text = text
        self.show_text = show_text
        self.setObjectName("TopBarButton")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(46)
        self.setMinimumWidth(116 if show_text else 56)
        self.setIcon(qta.icon(f'fa5s.{icon_name}'))
        self.setIconSize(QSize(24, 24))
        self.setText(text if show_text else "")
        self.setToolTip(text)
        self.setLayoutDirection(Qt.RightToLeft)
        self.badge = QLabel(str(badge_count) if badge_count > 0 else "")
        self.badge.setStyleSheet("""
            background-color: #ef4444;
            color: white;
            border-radius: 12px;
            padding: 2px 6px;
            font-size: 10px;
            font-weight: bold;
            margin-left: 4px;
        """)
        self.badge.setVisible(badge_count > 0)
        self.badge.move(self.width() - 20, 5)

    def resizeEvent(self, event):
        self.badge.move(self.width() - 25, 5)
        super().resizeEvent(event)

    def set_badge(self, count):
        self.badge.setText(str(count) if count > 0 else "")
        self.badge.setVisible(count > 0)

class ModernTopBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ModernTopBar")
        self.setMinimumHeight(72)
        try:
            self.setLayoutDirection(qt_layout_direction(settings_service.get_language()))
        except Exception:
            pass
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.buttons = {}
        self.menus = {}
        self.init_ui()

    def init_ui(self):
        """Build the utility strip below the ERP navigation menu.

        Phase 46 moves ERP navigation to the native QMenuBar and keeps this
        widget focused on global search, notifications, theme and user identity.
        """
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 8, 18, 10)
        outer.setSpacing(0)

        utility_frame = QFrame()
        utility_frame.setObjectName("ShellUtilityFrame")
        utility_layout = QHBoxLayout(utility_frame)
        utility_layout.setContentsMargins(12, 6, 12, 6)
        utility_layout.setSpacing(10)

        self.search_box = QLineEdit()
        self.search_box.setObjectName("GlobalSearchBox")
        self.search_box.setPlaceholderText(translate('global_search_placeholder'))
        self.search_box.setMinimumWidth(360)
        self.search_box.setMaximumWidth(620)
        self.search_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        utility_layout.addWidget(self.search_box, 2)

        utility_layout.addStretch(1)

        self.alert_btn = QToolButton()
        self.alert_btn.setObjectName("ShellIconButton")
        self.alert_btn.setIcon(qta.icon('fa5s.bell'))
        self.alert_btn.setIconSize(QSize(20, 20))
        self.alert_btn.setText('')
        self.alert_btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.alert_btn.setToolTip(translate('alerts'))
        self.alert_btn.setFixedSize(48, 48)
        self.alert_badge = QLabel('', self.alert_btn)
        self.alert_badge.setObjectName('ShellAlertBadge')
        self.alert_badge.setAlignment(Qt.AlignCenter)
        self.alert_badge.setFixedHeight(18)
        self.alert_badge.setMinimumWidth(18)
        self.alert_badge.setStyleSheet("""
            QLabel#ShellAlertBadge {
                background-color: #ef4444;
                color: white;
                border: 1px solid white;
                border-radius: 9px;
                padding: 0 5px;
                font-size: 10px;
                font-weight: 800;
            }
        """)
        self.alert_badge.hide()
        utility_layout.addWidget(self.alert_btn)

        self.theme_btn = QToolButton()
        self.theme_btn.setObjectName("ShellIconButton")
        self.theme_btn.setIcon(qta.icon('fa5s.adjust'))
        self.theme_btn.setIconSize(QSize(20, 20))
        self.theme_btn.setText('')
        self.theme_btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.theme_btn.setToolTip(translate('toggle_theme'))
        self.theme_btn.setFixedSize(48, 48)
        utility_layout.addWidget(self.theme_btn)

        self.screenshot_btn = QToolButton()
        self.screenshot_btn.setObjectName("ShellIconButton")
        self.screenshot_btn.setIcon(qta.icon('fa5s.camera'))
        self.screenshot_btn.setIconSize(QSize(20, 20))
        self.screenshot_btn.setText('')
        self.screenshot_btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.screenshot_btn.setToolTip(translate('export_screenshot'))
        self.screenshot_btn.setFixedSize(48, 48)
        utility_layout.addWidget(self.screenshot_btn)

        self.user_label = QLabel("")
        self.user_label.setObjectName("ShellUserLabel")
        self.user_label.setMinimumHeight(34)
        self.user_label.setMaximumWidth(280)
        self.user_label.setToolTip(translate('current_user'))
        utility_layout.addWidget(self.user_label)

        outer.addWidget(utility_frame)


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_alert_badge()

    def _position_alert_badge(self):
        try:
            if hasattr(self, 'alert_badge') and hasattr(self, 'alert_btn'):
                self.alert_badge.adjustSize()
                w = max(18, self.alert_badge.width())
                self.alert_badge.setFixedWidth(w)
                self.alert_badge.move(self.alert_btn.width() - w - 3, 3)
        except Exception:
            pass

    def set_alert_badge(self, count):
        """Show a numeric badge on the notification button when alerts exist."""
        try:
            count = int(count or 0)
        except Exception:
            count = 0
        if not hasattr(self, 'alert_badge'):
            return
        if count <= 0:
            self.alert_badge.hide()
            self.alert_btn.setProperty('hasAlerts', False)
        else:
            text = '99+' if count > 99 else str(count)
            self.alert_badge.setText(text)
            self.alert_badge.show()
            self.alert_badge.raise_()
            self.alert_btn.setProperty('hasAlerts', True)
            self._position_alert_badge()
        self.alert_btn.style().unpolish(self.alert_btn)
        self.alert_btn.style().polish(self.alert_btn)

    def add_menu_button(self, name, icon_name, menu_items):
        """Backward-compatible no-op navigation hook.

        ERP navigation now lives in MainWindow.setup_menus(). Older code may
        still call this method, so it returns a lightweight action-less button
        object without adding visual duplication to the utility strip.
        """
        btn = QToolButton(self)
        btn.setObjectName("TopBarButton")
        btn.setText(name)
        btn.setIcon(qta.icon(f'fa5s.{icon_name}'))
        menu = QMenu(btn)
        for item_text, item_icon, callback, shortcut in menu_items:
            action = menu.addAction(qta.icon(f'fa5s.{item_icon}'), item_text)
            if shortcut:
                action.setShortcut(shortcut)
            action.triggered.connect(callback)
        btn.setMenu(menu)
        self.menus[name] = btn
        return btn

    def add_button(self, name, icon_name, callback, badge_count=0, show_text=True):
        btn = TopBarButton(name, icon_name, badge_count, self, show_text)
        btn.clicked.connect(callback)
        self.buttons[name] = btn
        return btn

    def set_page_context(self, title: str, breadcrumb: str = ''):
        # Page title/breadcrumb strip removed in Phase 40. Kept as no-op for compatibility.
        return

    def set_user(self, username: str, role: str = ''):
        label = username or translate('user')
        display = f'👤 {label}'
        if role:
            display += f' · {role}'
        self.user_label.setText(display)
        self.user_label.setToolTip(display)

    def set_active(self, page_key: str):
        for key, btn in self.buttons.items():
            btn.setProperty('active', key == page_key)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        for key, btn in self.menus.items():
            btn.setProperty('active', key == page_key)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def set_badge(self, name, count):
        if name in self.buttons:
            self.buttons[name].set_badge(count)

    def apply_styles(self):
        """Apply theme-aware styling to the top navigation shell.

        This bar used to hard-code dark colors, so it stayed dark even when the
        global light theme was active. We now read all colors from ThemeManager
        and keep only the red notification badge as a semantic status color.
        """
        try:
            from theme_manager import ThemeManager
            c = {key: ThemeManager.get(key) for key in (
                'bg_window', 'bg_panel', 'card_bg', 'input_bg', 'text_primary',
                'text_secondary', 'text_muted', 'border', 'primary',
                'primary_hover', 'selection_bg', 'danger'
            )}
        except Exception:
            c = {
                'bg_window': '#ffffff', 'bg_panel': '#f8fafc', 'card_bg': '#ffffff',
                'input_bg': '#ffffff', 'text_primary': '#1e293b',
                'text_secondary': '#475569', 'text_muted': '#64748b',
                'border': '#e2e8f0', 'primary': '#4f46e5',
                'primary_hover': '#4338ca', 'selection_bg': '#4f46e5',
                'danger': '#ef4444'
            }

        self.setStyleSheet(f"""
            #ModernTopBar {{
                background-color: {c['bg_panel']};
                border-bottom: 1px solid {c['border']};
            }}
            #ShellUtilityFrame {{
                background-color: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 14px;
            }}
            #ShellNavFrame {{
                background-color: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 14px;
                padding: 2px;
            }}
            #ShellNavScroll, #ShellNavContent {{
                background-color: transparent;
            }}
            QScrollBar:horizontal {{
                height: 6px;
                background: transparent;
            }}
            QScrollBar::handle:horizontal {{
                background: {c['border']};
                border-radius: 3px;
            }}
            #ShellPageTitle {{
                color: {c['text_primary']};
                font-size: 20px;
                font-weight: 800;
            }}
            #ShellBreadcrumb {{
                color: {c['text_muted']};
                font-size: 13px;
            }}
            #ShellUserLabel {{
                color: {c['text_secondary']};
                background-color: {c['card_bg']};
                border: 1px solid {c['border']};
                border-radius: 14px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 11px;
            }}
            #ShellIconButton, #ShellMoreButton {{
                background-color: {c['card_bg']};
                color: {c['text_secondary']};
                border: 1px solid {c['border']};
                border-radius: 14px;
                padding: 6px;
            }}
            #ShellIconButton:hover, #ShellMoreButton:hover {{
                background-color: {c['bg_window']};
                border-color: {c['primary']};
                color: {c['primary']};
            }}
            #GlobalSearchBox {{
                background-color: {c['input_bg']};
                border: 1px solid {c['border']};
                border-radius: 16px;
                padding: 7px 12px;
                color: {c['text_primary']};
                selection-background-color: {c['selection_bg']};
            }}
            #GlobalSearchBox:focus {{ border: 1px solid {c['primary']}; }}
            #TopBarButton, QToolButton#TopBarButton {{
                background-color: transparent;
                border: none;
                border-radius: 10px;
                color: {c['text_secondary']};
                font-weight: bold;
                font-size: 13px;
                padding: 0 12px;
            }}
            #TopBarButton:hover, QToolButton#TopBarButton:hover {{
                background-color: {c['bg_window']};
                color: {c['primary']};
            }}
            #TopBarButton[active="true"], QToolButton#TopBarButton[active="true"] {{
                background-color: {c['primary']};
                color: white;
            }}
            QToolButton::menu-indicator {{ image: none; }}
            QMenu {{
                background-color: {c['card_bg']};
                color: {c['text_primary']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{ padding: 7px 32px 7px 22px; border-radius: 5px; }}
            QMenu::item:selected {{ background-color: {c['primary']}; color: white; }}
        """)
