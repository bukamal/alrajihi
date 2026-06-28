# -*- coding: utf-8 -*-
from PyQt5.QtGui import QPalette, QColor
from core.services.user_preferences_service import user_preferences_service

from theme.brand import get_tokens
from theme.qss import build_global_qss


class ThemeManager:
    """Application theme facade backed by the Al Rajhi design system.

    Keep this class as the compatibility layer used by existing widgets.
    New visual values must be added to theme/brand.py instead of duplicating
    literal colors across screens.
    """
    _current_theme = 'light'
    _app = None

    LIGHT = get_tokens('light')
    DARK = get_tokens('dark')

    @classmethod
    def init_app(cls, app, theme=None):
        cls._app = app
        cls.apply_theme(theme or cls.load_theme())

    @classmethod
    def load_theme(cls):
        theme = user_preferences_service.get_text('theme', 'light')
        return theme if theme in ('light', 'dark') else 'light'

    @classmethod
    def save_theme(cls, theme):
        if theme not in ('light', 'dark'):
            theme = 'light'
        user_preferences_service.set_text('theme', theme)

    @classmethod
    def colors(cls, theme=None):
        theme = theme or cls._current_theme
        return cls.DARK if theme == 'dark' else cls.LIGHT

    @classmethod
    def apply_theme(cls, theme='light', persist=False):
        theme = theme if theme in ('light', 'dark') else 'light'
        cls._current_theme = theme
        if persist:
            cls.save_theme(theme)
        colors = cls.colors(theme)
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(colors['bg_window']))
        palette.setColor(QPalette.WindowText, QColor(colors['text_primary']))
        palette.setColor(QPalette.Base, QColor(colors['bg_table']))
        palette.setColor(QPalette.AlternateBase, QColor(colors['bg_table_alt']))
        palette.setColor(QPalette.Text, QColor(colors['text_primary']))
        palette.setColor(QPalette.Button, QColor(colors['bg_panel']))
        palette.setColor(QPalette.ButtonText, QColor(colors['text_primary']))
        palette.setColor(QPalette.Highlight, QColor(colors['selection_bg']))
        palette.setColor(QPalette.HighlightedText, QColor(colors['selection_text']))
        if cls._app:
            cls._app.setPalette(palette)
            cls._app.setStyleSheet(cls._generate_stylesheet(colors))

    @classmethod
    def get_current_theme(cls):
        return cls._current_theme

    @classmethod
    def get(cls, key):
        return cls.colors().get(key, '')

    @classmethod
    def get_stylesheet(cls):
        return cls._generate_stylesheet(cls.colors())

    @classmethod
    def _generate_stylesheet(cls, colors):
        return build_global_qss(colors)
