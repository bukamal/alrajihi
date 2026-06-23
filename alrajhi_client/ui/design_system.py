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
from theme.brand import BRAND


class DesignSystem:
    # Phase 332: expose the same design tokens used by global QSS and shell
    # widgets.  This keeps dialogs/forms from drifting into local font sizes.
    RADIUS_SM = int(BRAND.get('radius_sm', 8))
    RADIUS_MD = int(BRAND.get('radius_md', 12))
    RADIUS_LG = int(BRAND.get('radius_lg', 18))
    SPACING_XS = int(BRAND.get('spacing_xs', 4))
    SPACING_SM = int(BRAND.get('spacing_sm', 8))
    SPACING_MD = int(BRAND.get('spacing_md', 14))
    SPACING_LG = int(BRAND.get('spacing_lg', 24))
    FONT_BODY_PT = int(BRAND.get('font_size_body_pt', 11))
    FONT_TABLE_PT = int(BRAND.get('font_size_table_pt', 10))
    FONT_CAPTION_PX = int(BRAND.get('font_size_caption_px', 11))
    FONT_VALUE_PX = int(BRAND.get('font_size_value_px', 13))
    FONT_TITLE_PX = int(BRAND.get('font_size_title_px', 20))
    FONT_HERO_PX = int(BRAND.get('font_size_hero_px', 25))
    BRAND_BUTTON_MIN_HEIGHT = int(BRAND.get('brand_button_min_height', 42))
    BRAND_LOGO_LOGIN_PX = int(BRAND.get('brand_logo_login_px', 96))
    BRAND_TAB_MIN_HEIGHT = int(BRAND.get('brand_tab_min_height', 38))

    @staticmethod
    def color(name: str, fallback: str = '') -> str:
        return ThemeManager.get(name) or fallback


    @staticmethod
    def brand_gradient() -> str:
        return (
            "qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"stop:0 {DesignSystem.color('brand_gradient_start', '#071A2E')},"
            f"stop:0.55 {DesignSystem.color('brand_gradient_mid', '#083A63')},"
            f"stop:1 {DesignSystem.color('brand_gradient_end', '#087D78')})"
        )

    @staticmethod
    def apply_visual_role(widget, role: str):
        try:
            widget.setProperty('visualRole', role)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        except Exception:
            pass
        return widget

    @staticmethod
    def brand_mark_label(text: str = '') -> QLabel:
        label = QLabel(text)
        label.setObjectName('brandMark')
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumHeight(DesignSystem.BRAND_LOGO_LOGIN_PX)
        return label

    @staticmethod
    def card_style(accent: bool = False) -> str:
        if accent:
            return f"""
                QFrame#startupCard {{
                    background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 {DesignSystem.color('brand_gradient_start', '#071A2E')},
                        stop:0.55 {DesignSystem.color('brand_gradient_mid', '#083A63')},
                        stop:1 {DesignSystem.color('brand_gradient_end', '#087D78')});
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
    def title(text: str, size: int | None = None) -> QLabel:
        label = QLabel(text)
        label.setObjectName('heroTitle')
        label.setAlignment(Qt.AlignCenter)
        px = int(size or DesignSystem.FONT_HERO_PX)
        label.setStyleSheet(f"font-size: {px}px; font-weight: 800; color: {DesignSystem.color('text_primary', '#1A202C')};")
        return label

    @staticmethod
    def subtitle(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName('heroSubtitle')
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        label.setStyleSheet(f"font-size: {DesignSystem.FONT_VALUE_PX}px; color: {DesignSystem.color('text_secondary', '#4A5568')};")
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
        btn.setMinimumHeight(DesignSystem.BRAND_BUTTON_MIN_HEIGHT)
        if icon is not None:
            btn.setIcon(icon)
        return btn

    @staticmethod
    def secondary_button(text: str, icon=None) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName('secondary')
        btn.setMinimumHeight(max(int(BRAND.get('action_button_min_height', 38)), DesignSystem.BRAND_BUTTON_MIN_HEIGHT - 2))
        if icon is not None:
            btn.setIcon(icon)
        return btn
