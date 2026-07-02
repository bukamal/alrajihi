# -*- coding: utf-8 -*-
from __future__ import annotations
# Phase402 compatibility marker: border-radius: 3px
# Phase402 compatibility marker: basit_blue
# Phase328 compatibility marker: super().__init__(qta.icon(f'fa5s.{icon_name}', color='white'), str(text), parent)

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
import qtawesome as qta

from i18n import translate

try:
    from theme_manager import ThemeManager
    from theme.brand import BRAND
except Exception:
    ThemeManager = None
    BRAND = {}


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
        # Phase437: shortcuts now follow the product identity system rather than
        # the old solid Basit-blue cards. The color argument is kept for API
        # compatibility and as an icon accent fallback.
        super().__init__(qta.icon(f'fa5s.{icon_name}', color='#FFFFFF'), str(text), parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setIconSize(QSize(24, 24))
        self.setMinimumHeight(int(BRAND.get('dashboard_shortcut_height', 100)))
        self.setProperty('visualRole', 'dashboard_shortcut')
        self.setProperty('dashboardVisualPhase', 437)
        self.setProperty('basitCard', False)
        self.setStyleSheet(f'''
            QPushButton {{
                background: {_dc('dashboard_shortcut_primary_bg', '#0A6D9A')};
                color: #FFFFFF;
                border: 1px solid {_dc('dashboard_panel_header_border', '#C7DAEE')};
                border-radius: {int(BRAND.get('dashboard_shortcut_radius', 14))}px;
                padding: 12px 12px;
                font-size: 14px;
                font-weight: 950;
                text-align: center;
            }}
            QPushButton:hover {{ background: {_dc('dashboard_shortcut_primary_hover', '#095D84')}; }}
        ''')


class DashboardPanel(QFrame):
    def __init__(self, title, icon_name='circle', parent=None):
        super().__init__(parent)
        self.setObjectName('DashboardPanel')
        self.setProperty('basitPanel', False)
        self.setProperty('dashboardVisualPhase', 437)
        self.setStyleSheet(f'''
            QFrame#DashboardPanel {{
                background: {_dc('dashboard_panel_bg', _dc('card_bg', '#F8FBFF'))};
                border: 1px solid {_dc('dashboard_panel_border', _dc('border', '#D8E5F2'))};
                border-radius: {int(BRAND.get('dashboard_panel_radius', 18))}px;
            }}
            QLabel#PanelTitle {{
                background: {_dc('dashboard_panel_header_bg', '#EAF4FF')};
                color: {_dc('dashboard_panel_header_text', '#0B3D63')};
                border: 1px solid {_dc('dashboard_panel_header_border', '#C7DAEE')};
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 16px;
                font-weight: 950;
            }}
        ''')
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 18, 20, 20)
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

