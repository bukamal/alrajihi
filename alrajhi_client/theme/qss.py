# -*- coding: utf-8 -*-
"""QSS/CSS generators for the Al Rajhi design system."""
from __future__ import annotations

from .brand import BRAND


def build_global_qss(colors: dict) -> str:
    radius_sm = BRAND['radius_sm']
    radius_md = BRAND['radius_md']
    radius_lg = BRAND['radius_lg']
    font = BRAND['font_family']
    body_pt = BRAND.get('font_size_body_pt', 11)
    table_pt = BRAND.get('font_size_table_pt', 10)
    caption_px = BRAND.get('font_size_caption_px', 11)
    value_px = BRAND.get('font_size_value_px', 13)
    title_px = BRAND.get('font_size_title_px', 20)
    hero_px = BRAND.get('font_size_hero_px', 25)
    nav_px = BRAND.get('nav_font_px', 12)
    action_px = BRAND.get('action_button_font_px', 12)
    input_min = BRAND.get('input_min_height', 34)
    table_header_padding = BRAND.get('table_header_padding', 10)
    table_cell_padding = BRAND.get('table_cell_padding', 7)
    return f"""
        QMainWindow, QDialog, QWidget {{
            background-color: {colors['bg_window']};
            color: {colors['text_primary']};
            font-family: {font};
            font-size: {body_pt}pt;
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
            font-size: {caption_px}px;
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
            font-size: {value_px}px;
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
            min-height: {input_min}px;
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
            padding: {table_cell_padding}px;
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
            padding: {table_header_padding}px;
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
            padding: {table_header_padding}px;
            font-weight: bold;
        }}

        QMenuBar {{
            background-color: {colors['bg_panel']};
            color: {colors['text_primary']};
            border-bottom: 1px solid {colors['border']};
            font-size: {nav_px}px;
            font-weight: 800;
        }}
        QMenuBar::item {{ padding: 10px 14px; border-radius: 8px; }}
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
            padding: 7px 9px;
            font-size: {action_px}px;
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
            font-size: {hero_px}px;
            font-weight: 800;
            color: {colors['text_primary']};
        }}
        QLabel#heroSubtitle, QLabel#sectionHint {{
            color: {colors['text_secondary']};
            font-size: {action_px}px;
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

        /* Phase 24: modern restaurant touch UI. */
        QWidget#restaurantDashboard {{
            background-color: {colors['bg_window']};
        }}
        QFrame#restaurantHeaderCard {{
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: {radius_lg}px;
        }}
        QLabel#restaurantDashboardTitle {{
            font-size: 24px;
            font-weight: 900;
            color: {colors['primary']};
        }}
        QLabel#restaurantModeBadge {{
            background-color: {colors['brand_soft']};
            color: {colors['primary']};
            border: 1px solid {colors['border']};
            border-radius: 16px;
            padding: 7px 14px;
            font-weight: 800;
        }}
        QPushButton#restaurantRefreshButton {{
            background-color: {colors['primary']};
            color: white;
            border: none;
            border-radius: {radius_md}px;
            padding: 10px 18px;
            font-size: 15px;
            font-weight: 900;
        }}
        QWidget#restaurantTableMap, QWidget#restaurantTableMapPane,
        QWidget#restaurantPOSPane, QWidget#restaurantPOSWidget {{
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: {radius_lg}px;
        }}
        QFrame#restaurantTableFilterBar, QFrame#restaurantTableCounterBar {{
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
        }}
        QLineEdit#restaurantTableSearchInput, QComboBox#restaurantTableStatusFilter,
        QComboBox#restaurantTableZoneFilter {{
            min-height: 34px;
            border: 1px solid {colors['border']};
            border-radius: {radius_sm}px;
            padding: 4px 8px;
            background-color: {colors['input_bg']};
            color: {colors['text_primary']};
        }}
        QLabel#restaurantTableEmptyLabel {{
            color: {colors['text_muted']};
            font-weight: 800;
            padding: 18px;
        }}
        QLabel#restaurantTableCounter_all, QLabel#restaurantTableCounter_free, QLabel#restaurantTableCounter_occupied,
        QLabel#restaurantTableCounter_kitchen, QLabel#restaurantTableCounter_ready, QLabel#restaurantTableCounter_payment,
        QLabel#restaurantTableCounter_reserved {{
            border: 1px solid {colors['border']};
            border-radius: {radius_sm}px;
            padding: 4px 6px;
            font-weight: 900;
            background-color: {colors['card_bg']};
        }}
        QLabel#restaurantPOSStateBadge {{
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 7px 12px;
            font-weight: 900;
            background-color: {colors['brand_soft']};
            color: {colors['text_primary']};
        }}
        QLabel#restaurantPOSStateBadge[restaurant_order_state="editing"] {{
            background-color: {colors['warning_soft']};
            border-color: {colors['warning']};
            color: {colors['warning']};
        }}
        QLabel#restaurantPOSStateBadge[restaurant_order_state="kitchen"] {{
            background-color: {colors['warning_soft']};
            border-color: {colors['warning']};
            color: {colors['warning']};
        }}
        QLabel#restaurantPOSStateBadge[restaurant_order_state="ready"] {{
            background-color: {colors['success_soft']};
            border-color: {colors['success']};
            color: {colors['success']};
        }}
        QLabel#restaurantPOSStateBadge[restaurant_order_state="payment_due"] {{
            background-color: {colors['brand_soft']};
            border-color: {colors['primary']};
            color: {colors['primary']};
        }}
        QLabel#restaurantPOSStateBadge[restaurant_order_state="paid"] {{
            background-color: {colors['success_soft']};
            border-color: {colors['success']};
            color: {colors['success']};
        }}
        QPushButton#restaurantTableButton {{
            border: 2px solid {colors['border']};
            border-radius: {radius_lg}px;
            padding: 18px;
            font-size: 17px;
            font-weight: 900;
            text-align: center;
            min-width: 170px;
            min-height: 120px;
        }}
        QPushButton#restaurantTableButton[restaurant_status="free"] {{
            background-color: {colors['success_soft']};
            color: {colors['success']};
            border-color: {colors['success']};
        }}
        QPushButton#restaurantTableButton[restaurant_status="occupied"] {{
            background-color: {colors['info_soft']};
            color: {colors['info']};
            border-color: {colors['info']};
        }}
        QPushButton#restaurantTableButton[restaurant_status="payment"] {{
            background-color: {colors['warning_soft']};
            color: {colors['warning']};
            border-color: {colors['warning']};
        }}
        QPushButton#restaurantTableButton[restaurant_status="reserved"] {{
            background-color: {colors['danger_soft']};
            color: {colors['danger']};
            border-color: {colors['danger']};
        }}
        QPushButton#restaurantTableButton[restaurant_status="kitchen"] {{
            background-color: {colors['warning_soft']};
            color: {colors['warning']};
            border-color: {colors['warning']};
        }}
        QPushButton#restaurantTableButton[restaurant_status="ready"] {{
            background-color: {colors['success_soft']};
            color: {colors['success']};
            border-color: {colors['success']};
        }}
        QPushButton#restaurantOrderModeButton, QPushButton#restaurantCafeModeButton, QPushButton#restaurantKitchenModeButton,
        QPushButton#restaurantAnalyticsModeButton {{
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 8px 14px;
            font-weight: 900;
        }}
        QPushButton#restaurantOrderModeButton[active="true"], QPushButton#restaurantCafeModeButton[active="true"], QPushButton#restaurantKitchenModeButton[active="true"],
        QPushButton#restaurantAnalyticsModeButton[active="true"] {{
            background-color: {colors['primary']};
            color: white;
            border-color: {colors['primary']};
        }}

        QFrame#restaurantTableOperationsBar {{
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: {radius_lg}px;
        }}
        QPushButton#restaurantTableOperationButton {{
            background-color: {colors['bg_table_alt']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 7px 12px;
            font-weight: 900;
        }}
        QPushButton#restaurantTableOperationButton:hover {{
            background-color: {colors['brand_soft']};
            color: {colors['primary']};
            border-color: {colors['primary']};
        }}
        QPushButton#restaurantTableOperationButton:disabled {{
            color: {colors['text_muted']};
            background-color: {colors['bg_table']};
        }}
        QToolButton#restaurantTableOperationsMenuButton {{
            background-color: {colors['primary']};
            color: white;
            border: none;
            border-radius: {radius_md}px;
            padding: 7px 14px;
            font-weight: 900;
        }}
        QSplitter#restaurantOperationSplitter[restaurant_layout_mode="compact"]::handle {{
            background-color: {colors['border']};
            width: 4px;
        }}
        QWidget#restaurantDashboard[restaurant_layout_mode="compact"] QLabel#restaurantDashboardTitle {{
            font-size: 18px;
        }}
        QWidget#restaurantDashboard[restaurant_layout_mode="compact"] QPushButton#restaurantOrderModeButton,
        QWidget#restaurantDashboard[restaurant_layout_mode="compact"] QPushButton#restaurantCafeModeButton,
        QWidget#restaurantDashboard[restaurant_layout_mode="compact"] QPushButton#restaurantKitchenModeButton,
        QWidget#restaurantDashboard[restaurant_layout_mode="compact"] QPushButton#restaurantAnalyticsModeButton,
        QWidget#restaurantDashboard[restaurant_layout_mode="compact"] QPushButton#restaurantRefreshButton {{
            padding: 6px 10px;
            font-size: {action_px}px;
        }}
        QLabel#restaurantMenuSectionTitle {{
            font-size: 15px;
            font-weight: 900;
            color: {colors['text_primary']};
        }}
        QPushButton#restaurantTableButton:hover {{
            background-color: {colors['brand_soft']};
            color: {colors['primary']};
            border-color: {colors['primary']};
        }}
        QLabel#restaurantPOSTitle {{
            font-size: 19px;
            font-weight: 900;
            color: {colors['text_primary']};
        }}
        QLabel#restaurantPOSTotal {{
            background-color: {colors['brand_soft']};
            color: {colors['primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 12px;
            font-size: 18px;
            font-weight: 900;
        }}
        QListWidget#restaurantOrderLines {{
            background-color: {colors['bg_table']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 8px;
            font-size: 15px;
        }}
        QListWidget#restaurantOrderLines::item {{
            min-height: 48px;
            padding: 9px;
            border-bottom: 1px solid {colors['border']};
        }}
        /* Phase 25: product-card ordering grid. */
        QLineEdit#restaurantMenuSearch {{
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 9px 14px;
            font-size: 15px;
        }}
        QPushButton#restaurantMenuSearchButton,
        QPushButton#restaurantManualItemButton {{
            background-color: {colors['card_bg']};
            color: {colors['primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 8px 14px;
            font-weight: 900;
        }}
        QScrollArea#restaurantMenuScroll {{
            background-color: {colors['bg_table']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
        }}
        QWidget#restaurantMenuHost {{
            background-color: {colors['bg_table']};
        }}
        QPushButton#restaurantMenuItemButton {{
            background-color: {colors['card_bg']};
            color: {colors['text_primary']};
            border: 2px solid {colors['border']};
            border-radius: {radius_lg}px;
            padding: 12px;
            font-size: 15px;
            font-weight: 900;
            text-align: center;
        }}
        QPushButton#restaurantMenuItemButton:hover {{
            background-color: {colors['brand_soft']};
            color: {colors['primary']};
            border-color: {colors['primary']};
        }}
        QLabel#restaurantEmptyMenuLabel {{
            color: {colors['text_secondary']};
            font-weight: 800;
            padding: 20px;
        }}

        /* Phase 309: Cafe workspace shell. */
        QFrame#restaurantCafeWorkspaceShell {{
            background-color: {colors['brand_soft']};
            border: 1px solid {colors['primary']};
            border-radius: {radius_lg}px;
        }}
        QLabel#restaurantCafeWorkspaceTitle {{
            color: {colors['text_primary']};
            font-size: 18px;
            font-weight: 900;
        }}
        QLabel#restaurantCafeWorkspaceSubtitle {{
            color: {colors['text_secondary']};
            font-size: {action_px}px;
            font-weight: 800;
        }}
        QPushButton#restaurantCafeQuickOrderButton,
        QPushButton#restaurantCafePreparationButton,
        QPushButton#restaurantCafeReportButton {{
            background-color: {colors['card_bg']};
            color: {colors['primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 7px 12px;
            font-weight: 900;
        }}
        QPushButton#restaurantCafeQuickOrderButton:hover,
        QPushButton#restaurantCafePreparationButton:hover,
        QPushButton#restaurantCafeReportButton:hover {{
            background-color: {colors['primary']};
            color: white;
            border-color: {colors['primary']};
        }}
        QWidget#restaurantPOSWidget[restaurant_order_context="cafe"] QFrame#restaurantOrderHeaderCard,
        QWidget#restaurantKitchenDisplay[restaurant_kds_context="cafe"] {{
            border-color: {colors['primary']};
        }}
        QLabel#restaurantCafeOptionsHeader {{
            background-color: {colors['brand_soft']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_lg}px;
            padding: 12px;
            font-size: 16px;
            font-weight: 900;
        }}
        QComboBox#restaurantCafeSizeCombo, QLineEdit#restaurantCafePreparationNotes {{
            background-color: {colors['card_bg']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 8px 10px;
            font-weight: 800;
        }}
        QLabel#restaurantCafeAddonGroupTitle {{
            color: {colors['primary']};
            font-size: {value_px}px;
            font-weight: 900;
            padding-top: 8px;
        }}
        QCheckBox#restaurantCafeModifierCheck {{
            color: {colors['text_primary']};
            font-weight: 800;
            padding: 4px 8px;
        }}
        QPushButton#restaurantKitchenButton {{ background-color: {colors['info']}; color: white; border: none; border-radius: {radius_md}px; font-weight: 900; }}
        QPushButton#restaurantPaymentButton {{ background-color: {colors['warning']}; color: white; border: none; border-radius: {radius_md}px; font-weight: 900; }}
        QPushButton#restaurantCloseButton {{ background-color: {colors['success']}; color: white; border: none; border-radius: {radius_md}px; font-weight: 900; }}
        QLabel#restaurantPOSStatus, QLabel#restaurantStatusBar {{
            color: {colors['text_secondary']};
            font-weight: 700;
            padding: 6px;
        }}

        /* Phase 28: restaurant kitchen display system. */
        QWidget#restaurantKitchenDisplay {{
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: {radius_lg}px;
        }}
        QLabel#restaurantKDSTitle,
        QLabel#restaurantKDSDetailTitle {{
            font-size: 18px;
            font-weight: 900;
            color: {colors['text_primary']};
        }}
        QListWidget#restaurantKDSTickets,
        QListWidget#restaurantKDSLines {{
            background-color: {colors['bg_table']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 8px;
            font-size: 15px;
            font-weight: 800;
        }}
        QListWidget#restaurantKDSTickets::item,
        QListWidget#restaurantKDSLines::item {{
            min-height: 56px;
            padding: 10px;
            border-bottom: 1px solid {colors['border']};
        }}

        QFrame#restaurantKDSBoardBody {{
            background-color: {colors['bg_table_alt']};
            border: 1px solid {colors['border']};
            border-radius: {radius_lg}px;
        }}

        QFrame#restaurantKDSDetailCard {{
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: {radius_lg}px;
            padding: 10px;
        }}
        QPushButton#restaurantKDSRefreshButton {{
            background-color: {colors['card_bg']};
            color: {colors['primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 8px 14px;
            font-weight: 900;
        }}
        QLabel#restaurantKDSStatus {{
            color: {colors['text_secondary']};
            font-weight: 700;
            padding: 6px;
        }}

        /* Phase 288: hardened restaurant KDS filters, counters and detail metadata. */
        QComboBox#restaurantKDSStatusFilter,
        QComboBox#restaurantKDSStationFilter {{
            background-color: {colors['card_bg']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 8px 12px;
            font-weight: 900;
            min-width: 150px;
        }}
        QLabel#restaurantKDSDetailMeta {{
            color: {colors['text_secondary']};
            font-weight: 800;
            padding: 4px 0 8px 0;
        }}


        /* Phase 292: restaurant current-order visual cleanup. */
        QFrame#restaurantOrderHeaderCard,
        QFrame#restaurantOrderSummaryCard,
        QFrame#restaurantActionGroups {{
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: {radius_lg}px;
        }}
        QLabel#restaurantSessionMeta,
        QLabel#restaurantGuestLabel {{
            color: {colors['text_secondary']};
            font-weight: 800;
        }}
        QFrame#restaurantOrderSummaryMetric {{
            background-color: {colors['bg_table_alt']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
        }}
        QLabel#restaurantOrderSummaryLabel {{
            color: {colors['text_secondary']};
            font-weight: 800;
            font-size: {action_px}px;
        }}
        QLabel#restaurantOrderSummaryValue_subtotal,
        QLabel#restaurantOrderSummaryValue_discount,
        QLabel#restaurantOrderSummaryValue_service_charge,
        QLabel#restaurantOrderSummaryValue_tax,
        QLabel#restaurantOrderSummaryValue_total,
        QLabel#restaurantOrderSummaryValue_paid,
        QLabel#restaurantOrderSummaryValue_remaining {{
            color: {colors['text_primary']};
            font-weight: 950;
            font-size: 15px;
        }}
        QLabel#restaurantOrderSummaryValue_total,
        QLabel#restaurantOrderSummaryValue_remaining {{
            color: {colors['primary']};
        }}
        QFrame#restaurantActionGroup {{
            background-color: {colors['bg_table_alt']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
        }}
        QLabel#restaurantActionGroupTitle {{
            color: {colors['text_secondary']};
            font-weight: 950;
            padding: 0 2px 2px 2px;
        }}
        QPushButton#restaurantKitchenPrintButton,
        QPushButton#restaurantAdjustButton,
        QPushButton#restaurantSplitBillButton,
        QPushButton#restaurantReceiptPrintButton {{
            background-color: {colors['card_bg']};
            color: {colors['primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            font-weight: 900;
        }}
        QPushButton#restaurantKitchenPrintButton:hover,
        QPushButton#restaurantAdjustButton:hover,
        QPushButton#restaurantSplitBillButton:hover,
        QPushButton#restaurantReceiptPrintButton:hover {{
            background-color: {colors['brand_soft']};
            border-color: {colors['primary']};
        }}

        QWidget#restaurantPOSWidget[restaurant_compact_mode="true"] QLabel#restaurantPOSTitle {{
            font-size: 15px;
        }}
        QWidget#restaurantPOSWidget[restaurant_compact_mode="true"] QLabel#restaurantSessionMeta {{
            font-size: {caption_px}px;
        }}
        QFrame#restaurantOrderSummaryCard[restaurant_compact_mode="true"] {{
            padding: 0px;
        }}
        QFrame#restaurantOrderSummaryCard[restaurant_compact_mode="true"] QLabel#restaurantOrderSummaryLabel {{
            font-size: {caption_px}px;
        }}
        QFrame#restaurantOrderSummaryCard[restaurant_compact_mode="true"] QLabel#restaurantOrderSummaryValue_total,
        QFrame#restaurantOrderSummaryCard[restaurant_compact_mode="true"] QLabel#restaurantOrderSummaryValue_paid,
        QFrame#restaurantOrderSummaryCard[restaurant_compact_mode="true"] QLabel#restaurantOrderSummaryValue_remaining {{
            font-size: {value_px}px;
        }}

        QLabel#restaurantKDSCounter_sent,
        QLabel#restaurantKDSCounter_preparing,
        QLabel#restaurantKDSCounter_ready,
        QLabel#restaurantKDSCounter_overdue {{
            background-color: {colors['bg_table_alt']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 8px 12px;
            font-weight: 900;
        }}


        /* Phase 326/328: compact one-row transaction header and horizontal footer. */
        QFrame#TransactionInlineHeaderBar {{
            background-color: {colors['bg_panel']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 4px;
        }}
        QFrame#TransactionInlineHeaderField {{
            background-color: transparent;
            border: none;
            padding: 0px;
        }}
        QLabel#TransactionInlineHeaderLabel {{
            color: {colors['text_secondary']};
            font-size: {caption_px}px;
            font-weight: 800;
            padding: 0px 1px;
        }}
        QFrame#TransactionFooterPanel {{
            background-color: transparent;
            border: none;
        }}
        QFrame#TransactionHorizontalSummaryFrame,
        QFrame#TransactionHorizontalPaymentFrame {{
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
        }}
        QLabel#TransactionSummaryCaption {{
            color: {colors['text_secondary']};
            font-size: {caption_px}px;
            font-weight: 800;
        }}
        QLabel#TransactionSummaryValue {{
            color: {colors['text_primary']};
            font-size: {caption_px}px;
            font-weight: 900;
        }}

        /* Phase 298: fullscreen restaurant operational shell. */
        QStackedWidget#restaurantFullscreenModeStack {{
            background-color: {colors['bg_window']};
            border: 1px solid {colors['border']};
            border-radius: {radius_lg}px;
        }}
        QWidget#restaurantOrderModePage,
        QWidget#restaurantKitchenModePage,
        QWidget#restaurantTablesModePage {{
            background-color: transparent;
        }}
        QSplitter#restaurantKitchenFullscreenSplitter[restaurant_layout_mode="compact"]::handle,
        QSplitter#restaurantOperationSplitter[restaurant_layout_mode="compact"]::handle {{
            background-color: {colors['border']};
            width: 6px;
        }}
        QPushButton#restaurantTablesModeButton[active="true"],
        QPushButton#restaurantKitchenModeButton[active="true"],
        QPushButton#restaurantCafeModeButton[active="true"],
        QPushButton#restaurantOrderModeButton[active="true"] {{
            background-color: {colors['primary']};
            color: white;
            border-color: {colors['primary']};
        }}
        QWidget#restaurantPOSWidget[restaurant_compact_mode="true"] QFrame#restaurantActionGroup {{
            padding: 0px;
        }}
        QWidget#restaurantPOSWidget[restaurant_compact_mode="true"] QPushButton#restaurantKitchenButton,
        QWidget#restaurantPOSWidget[restaurant_compact_mode="true"] QPushButton#restaurantPaymentButton,
        QWidget#restaurantPOSWidget[restaurant_compact_mode="true"] QPushButton#restaurantCloseButton,
        QWidget#restaurantPOSWidget[restaurant_compact_mode="true"] QPushButton#restaurantReceiptPrintButton,
        QWidget#restaurantPOSWidget[restaurant_compact_mode="true"] QPushButton#restaurantSplitBillButton,
        QWidget#restaurantPOSWidget[restaurant_compact_mode="true"] QPushButton#restaurantAdjustButton,
        QWidget#restaurantPOSWidget[restaurant_compact_mode="true"] QPushButton#restaurantKitchenPrintButton {{
            min-height: 46px;
            padding: 6px 8px;
        }}
        QPushButton#restaurantMenuItemButton {{
            text-align: center;
            padding: 8px;
            font-weight: 900;
        }}


        /* Phase 300: restaurant order header search and collapsible product grid. */
        QFrame#restaurantOrderSearchHeader {{
            background-color: {colors['bg_table_alt']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
        }}
        QLineEdit#restaurantOrderHeaderSearch {{
            background-color: {colors['card_bg']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 9px 14px;
            font-size: 15px;
            font-weight: 800;
        }}
        QPushButton#restaurantOrderHeaderSearchButton,
        QPushButton#restaurantHeaderManualItemButton {{
            background-color: {colors['card_bg']};
            color: {colors['primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 8px 13px;
            font-weight: 900;
        }}
        QPushButton#restaurantOrderHeaderSearchButton:hover,
        QPushButton#restaurantHeaderManualItemButton:hover {{
            background-color: {colors['brand_soft']};
            border-color: {colors['primary']};
        }}
        QFrame#restaurantMenuToggleCard {{
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
        }}
        QToolButton#restaurantMenuToggleButton {{
            background-color: {colors['bg_table_alt']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 7px 14px;
            font-weight: 950;
        }}
        QToolButton#restaurantMenuToggleButton:checked {{
            background-color: {colors['brand_soft']};
            color: {colors['primary']};
            border-color: {colors['primary']};
        }}
        QWidget#restaurantPOSWidget QFrame#restaurantOrderHeaderCard {{
            padding: 0px;
        }}
        QWidget#restaurantPOSWidget QTableView#restaurantOrderLines {{
            font-size: {value_px}px;
        }}


        /* Phase 344: runtime visual polish sweep.  These selectors are driven
           by safe dynamic properties applied by ui.runtime_visual_polish and
           intentionally cover old and new workspaces without local QSS drift. */
        QWidget[visualWorkspaceType="dashboard"], QWidget[visualWorkspaceType="list"],
        QWidget[visualWorkspaceType="document"], QWidget[visualWorkspaceType="operational"],
        QWidget[visualWorkspaceType="matrix"], QWidget[visualWorkspaceType="report"],
        QWidget[visualWorkspaceType="settings"] {{
            background-color: {colors['bg_window']};
            color: {colors['text_primary']};
        }}
        QFrame[visualRole="card"], QGroupBox[visualRole="card"] {{
            background-color: {colors['card_bg']};
            border: 1px solid {colors['border']};
            border-radius: {radius_lg}px;
        }}
        QTableView[visualRole="runtime_table"], QTableWidget[visualRole="runtime_table"] {{
            background-color: {colors['bg_table']};
            alternate-background-color: {colors['bg_table_alt']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            gridline-color: {colors['border']};
        }}
        QWidget[visualWorkspaceType="document"] QTableView[visualRole="runtime_table"],
        QWidget[visualWorkspaceType="report"] QTableView[visualRole="runtime_table"] {{
            font-size: {table_pt}pt;
        }}
        QWidget[visualWorkspaceType="operational"] QTableView[visualRole="runtime_table"] {{
            font-size: {value_px}px;
        }}
        QPushButton[visualRole="dashboard_shortcut"], QPushButton[visualRole="operation_action"] {{
            min-height: 44px;
            padding: 10px 14px;
            border-radius: {radius_md}px;
            font-weight: 900;
        }}
        QPushButton[visualRole="document_action"], QPushButton[visualRole="list_action"],
        QPushButton[visualRole="report_action"], QPushButton[visualRole="settings_action"],
        QPushButton[visualRole="matrix_action"] {{
            min-height: {BRAND.get('action_button_min_height', 38)}px;
            padding: 8px 13px;
            border-radius: {radius_sm}px;
            font-weight: 800;
        }}
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
