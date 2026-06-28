# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
import qtawesome as qta

from i18n import translate

try:
    from theme_manager import ThemeManager
except Exception:
    ThemeManager = None


def _dc(key, fallback):
    try:
        if ThemeManager:
            return ThemeManager.get(key) or fallback
    except Exception:
        pass
    return fallback


class KPIStatCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, value='0', icon_name='chart-line', color=None, hint='', parent=None):
        super().__init__(parent)
        color = color or _dc('primary', '#0F3D75')
        self.color = color
        self.setObjectName('KPIStatCard')
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(116)
        self.setStyleSheet(f'''
            QFrame#KPIStatCard {{
                background: {_dc('card_bg', '#FFFFFF')};
                border: 1px solid {_dc('border', '#E2E8F0')};
                border-radius: 18px;
            }}
            QFrame#KPIStatCard:hover {{
                border: 1px solid {color};
                background: {_dc('brand_soft', '#EAF1F8')};
            }}
            QLabel#KpiTitle {{
                color: {_dc('text_secondary', '#4A5568')};
                font-size: 13px;
                font-weight: 700;
            }}
            QLabel#KpiValue {{
                color: {_dc('text_primary', '#1A202C')};
                font-size: 24px;
                font-weight: 900;
            }}
            QLabel#KpiHint {{
                color: {_dc('text_muted', '#718096')};
                font-size: 11px;
            }}
            QLabel#KpiIcon {{
                background: {color};
                border-radius: 15px;
                padding: 8px;
            }}
        ''')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        top = QHBoxLayout()
        self.icon_label = QLabel()
        self.icon_label.setObjectName('KpiIcon')
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(42, 42)
        self.icon_label.setPixmap(qta.icon(f'fa5s.{icon_name}', color='white').pixmap(QSize(22, 22)))
        self.title_label = QLabel(title)
        self.title_label.setObjectName('KpiTitle')
        self.title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top.addWidget(self.icon_label)
        top.addWidget(self.title_label, 1)
        layout.addLayout(top)

        self.value_label = QLabel(value)
        self.value_label.setObjectName('KpiValue')
        self.value_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.value_label)

        self.hint_label = QLabel(hint)
        self.hint_label.setObjectName('KpiHint')
        self.hint_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.hint_label)

    def set_value(self, text):
        self.value_label.setText(text)

    def set_hint(self, text):
        self.hint_label.setText(text or '')

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        super().mouseReleaseEvent(event)


class QuickActionButton(QPushButton):
    def __init__(self, text, icon_name, color, parent=None):
        # Phase402: dashboard shortcuts use a Basit-inspired uniform blue card
        # surface. The legacy color argument is kept for API compatibility.
        super().__init__(qta.icon(f'fa5s.{icon_name}', color='white'), str(text), parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setIconSize(QSize(24, 24))
        self.setMinimumHeight(96)
        self.setProperty('visualRole', 'dashboard_shortcut')
        self.setProperty('basitCard', True)
        self.setStyleSheet(f'''
            QPushButton {{
                background: {_dc('basit_blue', _dc('primary', '#0F3D75'))};
                color: {_dc('basit_card_text', '#FFFFFF')};
                border: 1px solid {_dc('basit_card_border', _dc('primary', '#0F3D75'))};
                border-radius: 3px;
                padding: 10px 10px;
                font-size: 14px;
                font-weight: 950;
                text-align: center;
            }}
            QPushButton:hover {{ background: {_dc('basit_blue_hover', _dc('primary_hover', '#1E5AA8'))}; }}
        ''')


class DashboardPanel(QFrame):
    def __init__(self, title, icon_name='circle', parent=None):
        super().__init__(parent)
        self.setObjectName('DashboardPanel')
        self.setProperty('basitPanel', True)
        self.setStyleSheet(f'''
            QFrame#DashboardPanel {{
                background: {_dc('basit_table_bg', _dc('card_bg', '#FFFFFF'))};
                border: 1px solid {_dc('basit_toolbar_border', _dc('border', '#E2E8F0'))};
                border-radius: 2px;
            }}
            QLabel#PanelTitle {{
                background: {_dc('basit_yellow', '#F5C542')};
                color: {_dc('basit_category_text', '#1F2937')};
                border: 1px solid {_dc('basit_toolbar_border', _dc('border', '#E2E8F0'))};
                border-radius: 2px;
                padding: 7px 10px;
                font-size: 17px;
                font-weight: 950;
            }}
        ''')
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 16, 18, 18)
        self.layout.setSpacing(14)
        header = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(qta.icon(f'fa5s.{icon_name}', color=_dc('primary', '#0F3D75')).pixmap(QSize(20, 20)))
        title_label = QLabel(title)
        title_label.setObjectName('PanelTitle')
        title_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header.addWidget(icon)
        header.addWidget(title_label)
        header.addStretch()
        self.layout.addLayout(header)

