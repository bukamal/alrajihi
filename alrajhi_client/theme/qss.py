# -*- coding: utf-8 -*-
"""QSS/CSS generators for the Al Rajhi design system."""
from __future__ import annotations

from .brand import BRAND


def build_global_qss(colors: dict) -> str:
    radius_sm = BRAND['radius_sm']
    radius_md = BRAND['radius_md']
    radius_lg = BRAND['radius_lg']
    font = BRAND['font_family']
    return f"""
        QMainWindow, QDialog, QWidget {{
            background-color: {colors['bg_window']};
            color: {colors['text_primary']};
            font-family: {font};
            font-size: 10pt;
        }}
        QFrame#sidebar, QFrame#MainFrame, QFrame#card, QGroupBox {{
            background-color: {colors['bg_panel']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
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
        QLabel#fieldError {{
            color: {colors['danger']};
            font-size: 11px;
            padding: 1px 4px 5px 4px;
        }}
        QPushButton {{
            background-color: {colors['bg_panel']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_sm}px;
            padding: 7px 13px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            border-color: {colors['primary']};
            background-color: {colors['brand_soft']};
        }}
        QPushButton:disabled {{
            color: {colors['text_muted']};
            background-color: {colors['bg_panel']};
        }}
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
        QPushButton#secondary {{
            background-color: {colors['card_bg']};
            color: {colors['primary']};
            border: 1px solid {colors['primary']};
            border-radius: {radius_sm}px;
            padding: 8px 14px;
        }}
        QPushButton#secondary:hover {{
            background-color: {colors['brand_soft']};
        }}
        QPushButton#danger {{ background-color: {colors['danger']}; color: white; border: none; }}
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {{
            background-color: {colors['input_bg']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_sm}px;
            padding: 8px;
            selection-background-color: {colors['selection_bg']};
            selection-color: {colors['selection_text']};
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 2px solid {colors['border_focus']};
        }}
        QLineEdit[invalid="true"], QTextEdit[invalid="true"], QPlainTextEdit[invalid="true"],
        QComboBox[invalid="true"], QSpinBox[invalid="true"], QDoubleSpinBox[invalid="true"] {{
            border: 2px solid {colors['danger']};
            background-color: {colors['danger_soft']};
        }}
        QTableView, QTableWidget, QTreeView, QTreeWidget {{
            background-color: {colors['bg_table']};
            alternate-background-color: {colors['bg_table_alt']};
            color: {colors['text_primary']};
            gridline-color: {colors['border']};
            border: 1px solid {colors['border']};
            border-radius: {radius_sm}px;
            outline: 0;
            selection-background-color: {colors['selection_bg']};
            selection-color: {colors['selection_text']};
        }}
        QTableView::item, QTableWidget::item, QTreeView::item, QTreeWidget::item {{
            padding: 6px;
            border-bottom: 1px solid {colors['border']};
        }}
        QTableView::item:selected, QTableWidget::item:selected,
        QTreeView::item:selected, QTreeWidget::item:selected {{
            background-color: {colors['selection_bg']};
            color: {colors['selection_text']};
        }}
        QTableCornerButton::section {{
            background-color: {colors['header_bg']};
            border: none;
        }}
        QScrollBar:vertical, QScrollBar:horizontal {{
            background: {colors['bg_window']};
            border: none;
            margin: 0px;
        }}
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
            background: {colors['border']};
            border-radius: 5px;
            min-height: 24px;
            min-width: 24px;
        }}
        QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
            background: {colors['primary_2']};
        }}
        QHeaderView::section {{
            background-color: {colors['header_bg']};
            color: {colors['header_text']};
            padding: 8px;
            border: none;
            border-bottom: 1px solid {colors['border']};
            font-weight: bold;
            text-align: center;
        }}
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            background-color: {colors['bg_window']};
            border-radius: {radius_sm}px;
        }}
        QTabBar::tab {{
            background-color: {colors['bg_panel']};
            color: {colors['text_secondary']};
            padding: 8px 16px;
            margin-left: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }}
        QTabBar::tab:hover {{ background-color: {colors['brand_soft']}; color: {colors['primary']}; }}
        QTabBar::tab:selected {{ background-color: {colors['primary']}; color: white; font-weight: bold; }}

        /* Phase 73: safe table/tab coverage without runtime event filters. */
        QAbstractItemView {{
            background-color: {colors['bg_table']};
            alternate-background-color: {colors['bg_table_alt']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_sm}px;
            selection-background-color: {colors['selection_bg']};
            selection-color: {colors['selection_text']};
            outline: 0;
        }}
        QTableView::item:alternate, QTableWidget::item:alternate,
        QTreeView::item:alternate, QTreeWidget::item:alternate {{
            background-color: {colors['bg_table_alt']};
        }}
        QTableView::item:hover, QTableWidget::item:hover,
        QTreeView::item:hover, QTreeWidget::item:hover {{
            background-color: {colors['brand_soft']};
        }}
        QTableView QLineEdit, QTableWidget QLineEdit,
        QTableView QComboBox, QTableWidget QComboBox {{
            min-height: 26px;
            padding: 4px 6px;
            border-radius: 6px;
        }}
        QTableView QTableCornerButton::section,
        QTableWidget QTableCornerButton::section {{
            background-color: {colors['header_bg']};
            border: 0;
        }}
        QTabWidget QWidget {{
            background-color: {colors['bg_window']};
            color: {colors['text_primary']};
        }}
        QTabWidget > QWidget, QTabWidget QStackedWidget {{
            background-color: {colors['bg_window']};
            border: none;
        }}
        QTabWidget QFrame, QTabWidget QGroupBox {{
            background-color: {colors['bg_panel']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
        }}
        QTabWidget QTableView, QTabWidget QTableWidget,
        QDialog QTableView, QDialog QTableWidget {{
            background-color: {colors['bg_table']};
            alternate-background-color: {colors['bg_table_alt']};
            border: 1px solid {colors['border']};
            border-radius: {radius_sm}px;
            gridline-color: {colors['border']};
            selection-background-color: {colors['selection_bg']};
            selection-color: {colors['selection_text']};
        }}
        QTabWidget QHeaderView::section, QDialog QHeaderView::section {{
            background-color: {colors['header_bg']};
            color: {colors['header_text']};
            border: none;
            border-left: 1px solid {colors['border']};
            padding: 8px;
            font-weight: bold;
        }}

        QMenuBar {{
            background-color: {colors['bg_panel']};
            color: {colors['text_primary']};
            border-bottom: 1px solid {colors['border']};
        }}
        QMenuBar::item {{ padding: 7px 10px; border-radius: 6px; }}
        QMenuBar::item:selected, QMenu::item:selected {{ background-color: {colors['primary']}; color: white; }}
        QMenu {{
            background-color: {colors['bg_panel']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
        }}
        QToolBar {{
            background-color: {colors['bg_panel']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            spacing: 6px;
            padding: 6px;
        }}
        QToolButton {{
            background-color: transparent;
            color: {colors['text_primary']};
            border: 1px solid transparent;
            border-radius: {radius_sm}px;
            padding: 6px;
            font-weight: bold;
        }}
        QToolButton:hover {{
            background-color: {colors['brand_soft']};
            border-color: {colors['border']};
        }}
        QFrame#startupCard, QFrame#loginCard, QFrame#activationCard, QFrame#brandCard {{
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: {radius_lg}px;
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
        QProgressBar {{
            border: 1px solid {colors['border']};
            border-radius: 6px;
            text-align: center;
            background-color: {colors['bg_panel']};
            color: {colors['text_primary']};
        }}
        QProgressBar::chunk {{ background-color: {colors['primary']}; border-radius: 6px; }}
    """


def print_css_tokens(colors: dict) -> str:
    """Return CSS variables for HTML print templates."""
    return f"""
        :root {{
            --arj-primary: {colors['primary']};
            --arj-primary-2: {colors['primary_2']};
            --arj-accent: {colors['accent']};
            --arj-bg: {colors['bg_window']};
            --arj-card: {colors['card_bg']};
            --arj-text: {colors['text_primary']};
            --arj-muted: {colors['text_secondary']};
            --arj-border: {colors['border']};
            --arj-table-alt: {colors['bg_table_alt']};
            --arj-success: {colors['success']};
            --arj-warning: {colors['warning']};
            --arj-danger: {colors['danger']};
        }}
    """
