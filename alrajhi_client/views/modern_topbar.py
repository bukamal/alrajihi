# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QFrame, QToolButton, QMenu, QLineEdit, QScrollArea, QSizePolicy
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon
import qtawesome as qta

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
        self.setMinimumHeight(138)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.buttons = {}
        self.menus = {}
        self.init_ui()

    def init_ui(self):
        """Build a roomy, two-level application shell.

        The previous top bar placed page title, breadcrumb, global search,
        alerts, theme toggle, user identity and navigation buttons in a tight
        vertical block. On smaller screens the bar looked compressed after
        adding page/user context. This layout separates context from navigation
        and gives the nav row a horizontal scroll area instead of squeezing
        buttons.
        """
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 10, 18, 12)
        outer.setSpacing(8)

        # Context row: page title + breadcrumb on the right, utilities on the left.
        info_row = QHBoxLayout()
        info_row.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.page_title = QLabel("لوحة التحكم")
        self.page_title.setObjectName("ShellPageTitle")
        self.page_title.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.page_title.setWordWrap(False)
        self.breadcrumb = QLabel("الرئيسية")
        self.breadcrumb.setObjectName("ShellBreadcrumb")
        self.breadcrumb.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.breadcrumb.setWordWrap(False)
        title_box.addWidget(self.page_title)
        title_box.addWidget(self.breadcrumb)
        info_row.addLayout(title_box, 2)

        info_row.addStretch(1)

        self.search_box = QLineEdit()
        self.search_box.setObjectName("GlobalSearchBox")
        self.search_box.setPlaceholderText("بحث عام: مادة، عميل، فاتورة...")
        self.search_box.setMinimumWidth(260)
        self.search_box.setMaximumWidth(460)
        self.search_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        info_row.addWidget(self.search_box, 1)

        self.alert_btn = QToolButton()
        self.alert_btn.setObjectName("ShellIconButton")
        self.alert_btn.setIcon(qta.icon('fa5s.bell'))
        self.alert_btn.setIconSize(QSize(20, 20))
        self.alert_btn.setToolTip("التنبيهات")
        self.alert_btn.setFixedSize(38, 34)
        info_row.addWidget(self.alert_btn)

        self.theme_btn = QToolButton()
        self.theme_btn.setObjectName("ShellIconButton")
        self.theme_btn.setIcon(qta.icon('fa5s.adjust'))
        self.theme_btn.setIconSize(QSize(20, 20))
        self.theme_btn.setToolTip("تبديل الثيم")
        self.theme_btn.setFixedSize(38, 34)
        info_row.addWidget(self.theme_btn)

        self.user_label = QLabel("")
        self.user_label.setObjectName("ShellUserLabel")
        self.user_label.setMinimumHeight(32)
        self.user_label.setMaximumWidth(260)
        self.user_label.setToolTip("المستخدم الحالي")
        info_row.addWidget(self.user_label)

        outer.addLayout(info_row)

        # Navigation row: scrollable instead of compressed. Buttons keep readable sizes.
        nav_frame = QFrame()
        nav_frame.setObjectName("ShellNavFrame")
        nav_frame.setMinimumHeight(58)
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(8)

        self.nav_scroll = QScrollArea()
        self.nav_scroll.setObjectName("ShellNavScroll")
        self.nav_scroll.setWidgetResizable(True)
        self.nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nav_scroll.setFrameShape(QFrame.NoFrame)
        self.nav_scroll.setFixedHeight(58)

        self.nav_content = QWidget()
        self.nav_content.setObjectName("ShellNavContent")
        self.buttons_container = QHBoxLayout(self.nav_content)
        self.buttons_container.setContentsMargins(0, 0, 0, 0)
        self.buttons_container.setSpacing(8)
        self.buttons_container.addStretch(1)
        self.nav_scroll.setWidget(self.nav_content)
        nav_layout.addWidget(self.nav_scroll, 1)

        self.more_menu = QMenu(self)
        self.more_btn = QToolButton()
        self.more_btn.setObjectName("ShellMoreButton")
        self.more_btn.setIcon(qta.icon('fa5s.ellipsis-h'))
        self.more_btn.setIconSize(QSize(22, 22))
        self.more_btn.setMenu(self.more_menu)
        self.more_btn.setPopupMode(QToolButton.InstantPopup)
        self.more_btn.setToolTip("المزيد")
        self.more_btn.setFixedSize(48, 46)
        self.more_btn.setVisible(True)
        nav_layout.addWidget(self.more_btn)

        outer.addWidget(nav_frame)

    def add_menu_button(self, name, icon_name, menu_items):
        btn = QToolButton()
        btn.setIcon(qta.icon(f'fa5s.{icon_name}'))
        btn.setIconSize(QSize(24, 24))
        btn.setText(name)
        btn.setToolTip(name)
        btn.setLayoutDirection(Qt.RightToLeft)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(48)
        btn.setMinimumWidth(132)
        btn.setObjectName("TopBarButton")
        btn.setPopupMode(QToolButton.InstantPopup)
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        menu = QMenu()
        for item_text, item_icon, callback, shortcut in menu_items:
            action = menu.addAction(qta.icon(f'fa5s.{item_icon}'), item_text)
            if shortcut:
                action.setShortcut(shortcut)
            action.triggered.connect(callback)
        btn.setMenu(menu)

        self.buttons_container.insertWidget(max(0, self.buttons_container.count() - 1), btn)
        action = self.more_menu.addAction(qta.icon(f'fa5s.{icon_name}'), name)
        action.triggered.connect(lambda checked=False, b=btn: b.showMenu())
        self.menus[name] = btn
        return btn

    def add_button(self, name, icon_name, callback, badge_count=0, show_text=True):
        btn = TopBarButton(name, icon_name, badge_count, self, show_text)
        btn.clicked.connect(callback)
        self.buttons_container.insertWidget(max(0, self.buttons_container.count() - 1), btn)
        self.buttons[name] = btn
        action = self.more_menu.addAction(qta.icon(f'fa5s.{icon_name}'), name)
        action.triggered.connect(callback)
        return btn

    def set_page_context(self, title: str, breadcrumb: str = ''):
        self.page_title.setText(title or '')
        self.breadcrumb.setText(breadcrumb or title or '')

    def set_user(self, username: str, role: str = ''):
        label = username or 'مستخدم'
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
