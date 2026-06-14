# -*- coding: utf-8 -*-
"""Global UI design tokens and small helpers.

This module is intentionally lightweight.  It gives startup screens, dialogs,
and future widgets one visual language without coupling them to business logic.
"""
from __future__ import annotations

from PyQt5.QtWidgets import QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from theme_manager import ThemeManager


class DesignSystem:
    RADIUS_SM = 8
    RADIUS_MD = 12
    RADIUS_LG = 18
    SPACING_SM = 8
    SPACING_MD = 14
    SPACING_LG = 24

    @staticmethod
    def color(name: str, fallback: str = '') -> str:
        return ThemeManager.get(name) or fallback

    @staticmethod
    def card_style(accent: bool = False) -> str:
        if accent:
            return f"""
                QFrame#startupCard {{
                    background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 {DesignSystem.color('primary', '#0F3D75')},
                        stop:1 {DesignSystem.color('primary_2', '#1E5AA8')});
                    border-radius: {DesignSystem.RADIUS_LG}px;
                    border: 1px solid rgba(255,255,255,0.22);
                }}
            """
        return f"""
            QFrame#startupCard {{
                background-color: {DesignSystem.color('card_bg', '#ffffff')};
                border: 1px solid {DesignSystem.color('border', '#e2e8f0')};
                border-radius: {DesignSystem.RADIUS_LG}px;
            }}
        """

    @staticmethod
    def apply_shadow(widget, blur: int = 28, y: int = 10, alpha: int = 80):
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, y)
        shadow.setColor(QColor(0, 0, 0, alpha))
        widget.setGraphicsEffect(shadow)

    @staticmethod
    def title(text: str, size: int = 24) -> QLabel:
        label = QLabel(text)
        label.setObjectName('heroTitle')
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"font-size: {size}px; font-weight: 800; color: {DesignSystem.color('text_primary', '#1A202C')};")
        return label

    @staticmethod
    def subtitle(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName('heroSubtitle')
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet(f"font-size: 13px; color: {DesignSystem.color('text_secondary', '#4A5568')};")
        return label

    @staticmethod
    def status_pill(text: str, tone: str = 'info') -> QLabel:
        colors = {
            'info': ('info', 'info_soft'),
            'success': ('success', 'success_soft'),
            'warning': ('warning', 'warning_soft'),
            'danger': ('danger', 'danger_soft'),
        }
        fg_key, bg_key = colors.get(tone, colors['info'])
        label = QLabel(text)
        label.setObjectName('statusPill')
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"""
            QLabel#statusPill {{
                color: {DesignSystem.color(fg_key)};
                background-color: {DesignSystem.color(bg_key, 'rgba(59,130,246,0.10)')};
                border: 1px solid {DesignSystem.color(fg_key)};
                border-radius: 13px;
                padding: 5px 12px;
                font-weight: bold;
            }}
        """)
        return label

    @staticmethod
    def primary_button(text: str, icon=None) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName('primary')
        btn.setMinimumHeight(44)
        if icon is not None:
            btn.setIcon(icon)
        return btn

    @staticmethod
    def secondary_button(text: str, icon=None) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName('secondary')
        btn.setMinimumHeight(40)
        if icon is not None:
            btn.setIcon(icon)
        return btn
