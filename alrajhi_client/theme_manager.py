# -*- coding: utf-8 -*-
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import QSettings


class ThemeManager:
    _current_theme = 'light'
    _app = None

    LIGHT = {
        'bg_window': '#ffffff', 'bg_panel': '#f8fafc', 'bg_sidebar': '#f1f5f9',
        'bg_table': '#ffffff', 'bg_table_alt': '#f8fafc', 'text_primary': '#1e293b',
        'text_secondary': '#475569', 'text_muted': '#64748b', 'border': '#e2e8f0',
        'border_focus': '#4f46e5', 'primary': '#4f46e5', 'primary_hover': '#4338ca',
        'success': '#10b981', 'danger': '#ef4444', 'warning': '#f59e0b', 'info': '#3b82f6',
        'header_bg': '#f1f5f9', 'selection_bg': '#4f46e5', 'selection_text': '#ffffff',
        'card_bg': '#ffffff', 'input_bg': '#ffffff', 'primary_2': '#7c3aed',
        'success_soft': '#ecfdf5', 'warning_soft': '#fffbeb', 'danger_soft': '#fef2f2', 'info_soft': '#eff6ff',
        'shadow': 'rgba(15,23,42,0.16)'
    }

    DARK = {
        'bg_window': '#0f172a', 'bg_panel': '#1e293b', 'bg_sidebar': '#0f172a',
        'bg_table': '#1e293b', 'bg_table_alt': '#0f172a', 'text_primary': '#f8fafc',
        'text_secondary': '#cbd5e1', 'text_muted': '#94a3b8', 'border': '#334155',
        'border_focus': '#818cf8', 'primary': '#6366f1', 'primary_hover': '#4f46e5',
        'success': '#10b981', 'danger': '#f43f5e', 'warning': '#f59e0b', 'info': '#38bdf8',
        'header_bg': '#1e293b', 'selection_bg': '#4f46e5', 'selection_text': '#ffffff',
        'card_bg': '#111827', 'input_bg': '#111827', 'primary_2': '#a78bfa',
        'success_soft': 'rgba(16,185,129,0.16)', 'warning_soft': 'rgba(245,158,11,0.16)',
        'danger_soft': 'rgba(244,63,94,0.16)', 'info_soft': 'rgba(56,189,248,0.16)',
        'shadow': 'rgba(0,0,0,0.40)'
    }

    @classmethod
    def init_app(cls, app, theme=None):
        cls._app = app
        cls.apply_theme(theme or cls.load_theme())

    @classmethod
    def load_theme(cls):
        theme = QSettings('Alrajhi', 'Accounting').value('theme', 'light')
        return theme if theme in ('light', 'dark') else 'light'

    @classmethod
    def save_theme(cls, theme):
        if theme not in ('light', 'dark'):
            theme = 'light'
        QSettings('Alrajhi', 'Accounting').setValue('theme', theme)

    @classmethod
    def apply_theme(cls, theme='light', persist=False):
        theme = theme if theme in ('light', 'dark') else 'light'
        cls._current_theme = theme
        if persist:
            cls.save_theme(theme)
        colors = cls.LIGHT if theme == 'light' else cls.DARK
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
        colors = cls.LIGHT if cls._current_theme == 'light' else cls.DARK
        return colors.get(key, '')

    @classmethod
    def get_stylesheet(cls):
        colors = cls.LIGHT if cls._current_theme == 'light' else cls.DARK
        return cls._generate_stylesheet(colors)

    @classmethod
    def _generate_stylesheet(cls, colors):
        return f"""
            QMainWindow, QDialog, QWidget {{
                background-color: {colors['bg_window']};
                color: {colors['text_primary']};
                font-family: 'Tajawal', 'Segoe UI', sans-serif;
                font-size: 10pt;
            }}
            QFrame#sidebar, QFrame#MainFrame, QFrame#card, QGroupBox {{
                background-color: {colors['bg_panel']};
                border: 1px solid {colors['border']};
                border-radius: 10px;
            }}
            QGroupBox {{
                margin-top: 12px;
                padding: 12px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                right: 12px;
                padding: 0 6px;
                color: {colors['text_secondary']};
            }}
            QLabel#hint, QLabel#muted {{ color: {colors['text_muted']}; }}
            QLabel#danger {{ color: {colors['danger']}; }}
            QLabel#success {{ color: {colors['success']}; }}
            QPushButton {{
                background-color: {colors['bg_panel']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 7px 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {colors['border']}; }}
            QPushButton:disabled {{ color: {colors['text_muted']}; background-color: {colors['bg_panel']}; }}
            QPushButton#primary {{
                background-color: {colors['primary']};
                color: white;
                border: none;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                min-height: 40px;
            }}
            QPushButton#primary:hover {{ background-color: {colors['primary_hover']}; }}
            QPushButton#danger {{ background-color: {colors['danger']}; color: white; border: none; }}
            QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
                background-color: {colors['input_bg']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 7px;
                padding: 8px;
                selection-background-color: {colors['primary']};
            }}
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid {colors['border_focus']};
            }}
            QLineEdit[invalid="true"], QTextEdit[invalid="true"], QPlainTextEdit[invalid="true"],
            QComboBox[invalid="true"], QSpinBox[invalid="true"], QDoubleSpinBox[invalid="true"] {{
                border: 2px solid {colors['danger']};
                background-color: rgba(198, 40, 40, 0.06);
            }}
            QLabel#fieldError {{
                color: {colors['danger']};
                font-size: 11px;
                padding: 1px 4px 5px 4px;
            }}
            QTableView, QTableWidget {{
                background-color: {colors['bg_table']};
                alternate-background-color: {colors['bg_table_alt']};
                color: {colors['text_primary']};
                gridline-color: {colors['border']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                outline: 0;
            }}
            QHeaderView::section {{
                background-color: {colors['header_bg']};
                color: {colors['text_secondary']};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {colors['border']};
                font-weight: bold;
                text-align: center;
            }}
            QTabWidget::pane {{ border: 1px solid {colors['border']}; background-color: {colors['bg_window']}; border-radius: 8px; }}
            QTabBar::tab {{ background-color: {colors['bg_panel']}; color: {colors['text_secondary']}; padding: 8px 16px; margin-left: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }}
            QTabBar::tab:selected {{ background-color: {colors['primary']}; color: white; }}
            QMenuBar {{ background-color: {colors['bg_panel']}; color: {colors['text_primary']}; border-bottom: 1px solid {colors['border']}; }}
            QMenuBar::item:selected, QMenu::item:selected {{ background-color: {colors['primary']}; color: white; }}
            QMenu {{ background-color: {colors['bg_window']}; color: {colors['text_primary']}; border: 1px solid {colors['border']}; }}

            QFrame#startupCard, QFrame#loginCard, QFrame#activationCard {{
                background-color: {colors['card_bg']};
                border: 1px solid {colors['border']};
                border-radius: 18px;
            }}
            QLabel#heroTitle {{
                font-size: 25px;
                font-weight: 800;
                color: {colors['text_primary']};
            }}
            QLabel#heroSubtitle, QLabel#sectionHint {{
                color: {colors['text_secondary']};
                font-size: 12px;
            }}
            QLabel#statusPill {{
                border-radius: 13px;
                padding: 5px 12px;
                font-weight: bold;
            }}
            QPushButton#secondary {{
                background-color: {colors['card_bg']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
                padding: 8px 14px;
            }}
            QPushButton#secondary:hover {{
                border-color: {colors['primary']};
                color: {colors['primary']};
            }}

            QProgressBar {{ border: 1px solid {colors['border']}; border-radius: 6px; text-align: center; background-color: {colors['bg_panel']}; color: {colors['text_primary']}; }}
            QProgressBar::chunk {{ background-color: {colors['primary']}; border-radius: 6px; }}
        """
