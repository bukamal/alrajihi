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
    footer_px = BRAND.get('transaction_footer_font_px', value_px)
    footer_value_px = BRAND.get('transaction_footer_value_font_px', value_px)
    footer_action_px = BRAND.get('transaction_footer_action_font_px', action_px)
    footer_action_min = BRAND.get('transaction_footer_action_min_height', 44)
    brand_table_row_height = BRAND.get('brand_table_row_height', 38)
    brand_table_header_min_height = BRAND.get('brand_table_header_min_height', 42)
    brand_table_current_border = BRAND.get('brand_table_current_border_px', 2)
    transaction_footer_min = BRAND.get('transaction_footer_panel_min_height', 88)
    transaction_summary_min = BRAND.get('transaction_footer_summary_min_height', 74)
    transaction_button_min_width = BRAND.get('transaction_footer_button_min_width', 126)
    table_header_padding = BRAND.get('table_header_padding', 10)
    table_cell_padding = BRAND.get('table_cell_padding', 7)
    tab_min_height = BRAND.get('brand_tab_min_height', 38)
    tab_padding_x = BRAND.get('brand_tab_padding_x', 18)
    brand_button_min = BRAND.get('brand_button_min_height', 42)
    dialog_header_height = BRAND.get('brand_dialog_header_height', 58)
    return f"""
        QMainWindow, QDialog, QWidget {{
            background-color: {colors.get('surface_root', colors['bg_window'])};
            color: {colors['text_primary']};
            font-family: {font};
            font-size: {body_pt}pt;
        }}
        QFrame#sidebar, QFrame#MainFrame, QFrame#card, QGroupBox {{
            background-color: {colors.get('surface_raised', colors['bg_panel'])};
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
            min-height: {brand_button_min}px;
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
        QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
            border: 2px solid {colors['border_focus']};
            background-color: {colors.get('input_focus_bg', colors['input_bg'])};
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

        /* Phase349: active field highlight for editable entry grids. */
        QTableView[standard_table_keyboard="true"]::item:focus,
        QTableWidget[standard_table_keyboard="true"]::item:focus,
        QTableView[current_cell_highlight="true"]::item:focus,
        QTableWidget[current_cell_highlight="true"]::item:focus,
        QTableView#TransactionLineGrid::item:focus {{
            background-color: {colors.get('current_cell_bg', colors['warning_soft'])};
            color: {colors['text_primary']};
            border: 2px solid {colors.get('current_cell_border', colors['primary'])};
        }}
        QTableView[standard_table_keyboard="true"] QLineEdit:focus,
        QTableWidget[standard_table_keyboard="true"] QLineEdit:focus,
        QTableView#TransactionLineGrid QLineEdit:focus {{
            background-color: {colors.get('current_cell_bg', colors['warning_soft'])};
            border: 2px solid {colors.get('current_cell_border', colors['primary'])};
            selection-background-color: {colors['primary']};
            selection-color: white;
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
            background-color: {colors.get('table_header_bg', colors['header_bg'])};
            color: {colors.get('table_header_text', colors['header_text'])};
            padding: {table_header_padding}px;
            border: none;
            border-bottom: 1px solid {colors['border']};
            font-weight: bold;
            text-align: center;
        }}
        /* Phase352: branded main/sub tab labels. */
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            background-color: {colors.get('surface_root', colors['bg_window'])};
            border-radius: {radius_md}px;
            top: -1px;
        }}
        QTabBar::tab {{
            background-color: {colors.get('tab_inactive_bg', colors['bg_panel'])};
            color: {colors.get('tab_inactive_text', colors['text_secondary'])};
            padding: 8px {tab_padding_x}px;
            min-height: {tab_min_height}px;
            margin-left: 3px;
            border: 1px solid {colors['border']};
            border-top-left-radius: {radius_md}px;
            border-top-right-radius: {radius_md}px;
            font-weight: 800;
        }}
        QTabBar::tab:hover {{
            background-color: {colors['brand_soft']};
            color: {colors['primary']};
            border-color: {colors['primary']};
        }}
        QTabBar::tab:selected {{
            background-color: {colors.get('tab_active_bg', colors['primary'])};
            color: {colors.get('tab_active_text', '#FFFFFF')};
            border-color: {colors.get('tab_active_bg', colors['primary'])};
            font-weight: 900;
        }}
        QTabBar::close-button:hover {{
            background-color: {colors.get('tab_close_hover_bg', colors['danger'])};
            border-radius: 7px;
        }}

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
        /* Phase439/440: project-wide visual identity enforcement for all workspaces/tabs. */
        QWidget[projectVisualIdentityPhase="439"], QWidget[projectVisualIdentityPhase="440"], QWidget[projectVisualIdentityPhase="441"], QWidget[projectVisualIdentityPhase="442"], QWidget[projectVisualIdentityPhase="445"], QWidget[projectVisualIdentityPhase="447"], QWidget[projectVisualIdentityPhase="450"],
        QWidget[visualIdentitySweepPhase="440"], QWidget[visualIdentitySweepPhase="441"], QWidget[visualIdentitySweepPhase="442"], QWidget[visualIdentitySweepPhase="445"], QWidget[visualIdentitySweepPhase="447"], QWidget[visualIdentitySweepPhase="450"], QWidget[visualIdentitySweepPhase="450"] {{
            background-color: {colors.get('workspace_surface_bg', colors.get('surface_root', colors['bg_window']))};
            color: {colors['text_primary']};
        }}
        QWidget[visualRole="workspace_surface"], QWidget[visualRole="workspace_content"] {{
            background-color: {colors.get('workspace_content_bg', colors.get('surface_root', colors['bg_window']))};
            color: {colors['text_primary']};
        }}
        QFrame[visualRole="workspace_card"], QGroupBox[visualRole="workspace_card"],
        QFrame[visualRole="runtime_card"], QGroupBox[visualRole="runtime_card"] {{
            background-color: {colors.get('workspace_card_bg', colors.get('card_bg', colors['bg_panel']))};
            border: 1px solid {colors.get('workspace_card_border', colors['border'])};
            border-radius: {BRAND.get('workspace_card_radius', radius_md)}px;
        }}
        QLabel[visualRole="section_header"] {{
            background-color: {colors.get('workspace_section_header_bg', colors['brand_soft'])};
            color: {colors.get('workspace_section_header_text', colors['primary'])};
            border: 1px solid {colors.get('workspace_card_border', colors['border'])};
            border-radius: {radius_md}px;
            padding: 7px 12px;
            font-weight: 900;
        }}
        QPushButton[visualRole="workspace_action"] {{
            min-height: {BRAND.get('action_button_min_height', 38)}px;
            border-radius: {radius_sm}px;
            font-weight: 850;
        }}
        QScrollArea[visualRole="workspace_scroll"], QStackedWidget[visualRole="workspace_stack"] {{
            background-color: {colors.get('workspace_scroll_bg', colors.get('workspace_content_bg', colors['bg_window']))};
            border: none;
        }}
        QScrollArea[visualRole="workspace_scroll"] > QWidget > QWidget {{
            background-color: {colors.get('workspace_scroll_bg', colors.get('workspace_content_bg', colors['bg_window']))};
        }}
        QSplitter[visualRole="workspace_splitter"]::handle {{
            background-color: {colors.get('workspace_splitter_handle', colors.get('workspace_card_border', colors['border']))};
            border-radius: 3px;
        }}
        QWidget[visualStyleSource="centralized_runtime_visual_identity"] QFrame[visualRole="workspace_card"] {{
            padding: 1px;
        }}
        /* Phase441: semantic visual states replace hard-coded local status styles. */
        QLabel[visualStyleSource="centralized_visual_state"],
        QFrame[visualStyleSource="centralized_visual_state"] QLabel {{
            background: transparent;
            border: none;
        }}
        QLabel[visualRole="semantic_status"][visualStateSize="caption"] {{
            font-size: {caption_px}px;
            padding: 2px 4px;
        }}
        QLabel[visualStateWeight="strong"] {{ font-weight: 800; }}
        QLabel[visualState="muted"] {{ color: {colors['text_muted']}; }}
        QLabel[visualState="default"] {{ color: {colors['text_secondary']}; }}
        QLabel[visualState="success"] {{ color: {colors['success']}; }}
        QLabel[visualState="warning"] {{ color: {colors['warning']}; }}
        QLabel[visualState="danger"] {{ color: {colors['danger']}; }}
        QLabel[visualState="info"] {{ color: {colors['info']}; }}
        QLabel[visualRole="semantic_error_card"] {{
            background-color: {colors.get('danger_soft', colors.get('brand_soft', colors['bg_panel']))};
            color: {colors['danger']};
            border: 1px solid {colors['danger']};
            border-radius: {radius_md}px;
            padding: 24px;
            font-size: 15px;
            font-weight: 800;
        }}
        QLabel[visualRole="table_column_header"] {{
            background-color: {colors.get('workspace_section_header_bg', colors['brand_soft'])};
            color: {colors.get('workspace_section_header_text', colors['primary'])};
            border: 1px solid {colors.get('workspace_card_border', colors['border'])};
            border-radius: {radius_sm}px;
            padding: 6px 8px;
            font-weight: 900;
        }}
        QLabel[visualRole="camera_preview"] {{
            background-color: {colors.get('surface_sunken', colors['bg_table_alt'])};
            color: {colors.get('text_secondary', colors['text_primary'])};
            border: 1px solid {colors.get('workspace_card_border', colors['border'])};
            border-radius: {radius_md}px;
            padding: 10px;
            font-weight: 800;
        }}
        QFrame[visualState="success"] {{
            background-color: {colors.get('success_soft', colors.get('brand_soft', colors['bg_panel']))};
            border: 1px solid {colors['success']};
            border-radius: {radius_md}px;
        }}
        QFrame[visualState="warning"] {{
            background-color: {colors.get('warning_soft', colors.get('brand_soft', colors['bg_panel']))};
            border: 1px solid {colors['warning']};
            border-radius: {radius_md}px;
        }}
        QFrame[visualState="danger"] {{
            background-color: {colors.get('danger_soft', colors.get('brand_soft', colors['bg_panel']))};
            border: 1px solid {colors['danger']};
            border-radius: {radius_md}px;
        }}
        QFrame[visualState="info"] {{
            background-color: {colors.get('info_soft', colors.get('brand_soft', colors['bg_panel']))};
            border: 1px solid {colors['info']};
            border-radius: {radius_md}px;
        }}

        /* Phase445: materials workspace/list/editor visual identity migration. */
        QWidget[materialsVisualPhase="445"], QWidget[visualWorkspaceType="materials"] {{
            background-color: {colors.get('workspace_content_bg', colors['bg_window'])};
            color: {colors['text_primary']};
        }}
        QFrame#MaterialsFilterCard, QWidget[materialsFilterSurface="445"] {{
            background-color: {BRAND.get('materials_filter_card_bg', colors.get('workspace_card_bg', colors['bg_panel']))};
            border: 1px solid {BRAND.get('materials_filter_card_border', colors.get('workspace_card_border', colors['border']))};
            border-radius: {BRAND.get('workspace_card_radius', radius_lg)}px;
            padding: 6px;
        }}
        QLabel[visualRole="materials_filter_label"] {{
            background: transparent;
            color: {colors.get('text_secondary', colors['text_primary'])};
            font-weight: 800;
            padding: 0 4px;
        }}
        QComboBox[visualRole="materials_filter"], QLineEdit[visualRole="materials_search"] {{
            min-height: 34px;
            border-radius: {radius_sm}px;
            border: 1px solid {colors.get('workspace_card_border', colors['border'])};
            background-color: {colors.get('input_bg', colors['bg_panel'])};
            color: {colors['text_primary']};
            padding: 4px 8px;
        }}
        QWidget[visualRole="materials_toolbar"], QWidget[visualRole="materials_toolbar"] QPushButton {{
            border-radius: {radius_sm}px;
        }}
        QTableView[visualRole="materials_table"] QHeaderView::section,
        QTableWidget[visualRole="materials_table"] QHeaderView::section {{
            background-color: {BRAND.get('materials_table_header_bg', colors.get('header_bg', colors['primary']))};
            color: {BRAND.get('materials_table_header_text', colors.get('header_text', '#ffffff'))};
            font-weight: 900;
            padding: 8px;
            border: none;
            border-left: 1px solid {colors.get('workspace_card_border', colors['border'])};
        }}
        QGroupBox[visualRole="material_form_card"], QFrame[visualRole="material_form_card"] {{
            background-color: {colors.get('workspace_card_bg', colors['bg_panel'])};
            border: 1px solid {colors.get('workspace_card_border', colors['border'])};
            border-radius: {BRAND.get('materials_editor_card_radius', radius_lg)}px;
            margin-top: 16px;
            padding: 18px 14px 14px 14px;
            font-weight: 850;
            color: {colors['text_primary']};
        }}
        QGroupBox[visualRole="material_form_card"]::title {{
            subcontrol-origin: margin;
            right: 16px;
            padding: 0 10px;
            color: {colors.get('workspace_section_header_text', colors['primary'])};
            background-color: {colors.get('workspace_card_bg', colors['bg_panel'])};
            font-weight: 900;
        }}
        QFrame#MaterialEditorActionBar, QFrame[visualRole="material_action_bar"] {{
            background-color: {colors.get('workspace_card_bg', colors['bg_panel'])};
            border: 1px solid {colors.get('workspace_card_border', colors['border'])};
            border-radius: {BRAND.get('workspace_card_radius', radius_lg)}px;
        }}
        QWidget[visualRole="material_editor"] QLineEdit,
        QWidget[visualRole="material_editor"] QComboBox,
        QWidget[visualRole="material_editor"] QDoubleSpinBox,
        QWidget[visualRole="material_editor"] QSpinBox {{
            min-height: 36px;
            border-radius: {radius_sm}px;
            border: 1px solid {colors.get('workspace_card_border', colors['border'])};
            background-color: {colors.get('input_bg', colors['bg_panel'])};
            color: {colors['text_primary']};
            padding: 5px 9px;
        }}
        QWidget[visualRole="material_editor"] QLineEdit:focus,
        QWidget[visualRole="material_editor"] QComboBox:focus,
        QWidget[visualRole="material_editor"] QDoubleSpinBox:focus,
        QWidget[visualRole="material_editor"] QSpinBox:focus {{
            border: 1px solid {colors.get('border_focus', colors['primary'])};
        }}
        QWidget[visualRole="material_editor"] QPushButton#primary {{
            background-color: {BRAND.get('materials_editor_primary_action_bg', colors['primary'])};
            color: white;
            border: 1px solid {BRAND.get('materials_editor_primary_action_bg', colors['primary'])};
            font-weight: 900;
        }}
        QWidget[visualRole="material_editor"] QPushButton#primary:hover {{
            background-color: {BRAND.get('materials_editor_primary_action_hover', colors['primary_hover'])};
        }}
        QTabWidget[projectVisualIdentityPhase="439"]::pane,
        QTabWidget[projectVisualIdentityPhase="440"]::pane,
        QTabWidget[projectVisualIdentityPhase="441"]::pane,
        QTabWidget[projectVisualIdentityPhase="442"]::pane,
        QTabWidget[projectVisualIdentityPhase="445"]::pane,
        QTabWidget[projectVisualIdentityPhase="447"]::pane,
        QTabWidget[projectVisualIdentityPhase="450"]::pane,
        QTabWidget[projectVisualIdentityPhase="450"]::pane {{
            border: 1px solid {colors.get('workspace_card_border', colors['border'])};
            background-color: {colors.get('workspace_content_bg', colors['bg_window'])};
            border-radius: {BRAND.get('workspace_tab_radius', radius_md)}px;
        }}
        QTabWidget[projectVisualIdentityPhase="439"] QTabBar::tab,
        QTabWidget[projectVisualIdentityPhase="440"] QTabBar::tab,
        QTabWidget[projectVisualIdentityPhase="441"] QTabBar::tab,
        QTabWidget[projectVisualIdentityPhase="442"] QTabBar::tab,
        QTabWidget[projectVisualIdentityPhase="445"] QTabBar::tab,
        QTabWidget[projectVisualIdentityPhase="447"] QTabBar::tab,
        QTabWidget[projectVisualIdentityPhase="450"] QTabBar::tab,
        QTabWidget[projectVisualIdentityPhase="450"] QTabBar::tab {{
            min-height: {BRAND.get('workspace_tab_min_height', tab_min_height)}px;
            border-radius: {BRAND.get('workspace_tab_radius', radius_md)}px;
            margin: 3px;
        }}
        QWidget#DashboardResponsiveGridHost {{
            background: transparent;
            border: none;
        }}
        QWidget#DashboardResponsiveGridHost[dashboardResponsiveColumns="1"] QFrame#DashboardPanel {{
            min-width: 0px;
        }}
        QWidget#DashboardResponsiveGridHost[dashboardResponsiveColumns="2"] QFrame#DashboardPanel {{
            min-width: 0px;
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
            background-color: {colors.get('table_header_bg', colors['header_bg'])};
            color: {colors.get('table_header_text', colors['header_text'])};
            border: none;
            border-left: 1px solid {colors['border']};
            padding: {table_header_padding}px;
            font-weight: bold;
        }}

        /* Phase352: branded menu and action chrome. */
        QMenuBar {{
            background-color: {colors.get('menu_bg', colors['bg_panel'])};
            color: {colors['text_primary']};
            border-bottom: 1px solid {colors.get('menu_border', colors['border'])};
            font-size: {nav_px}px;
            font-weight: 900;
            min-height: 34px;
        }}
        QMenuBar::item {{ padding: 11px 16px; border-radius: {radius_sm}px; }}
        QMenuBar::item:selected, QMenu::item:selected {{
            background-color: {colors.get('menu_active_bg', colors['primary'])};
            color: {colors.get('menu_active_text', '#FFFFFF')};
        }}
        QMenu {{
            background-color: {colors.get('menu_bg', colors['bg_panel'])};
            color: {colors['text_primary']};
            border: 1px solid {colors.get('menu_border', colors['border'])};
            padding: 6px;
        }}
        QMenu::item {{ min-height: 28px; padding: 7px 18px; border-radius: {radius_sm}px; }}
        QToolBar {{
            background-color: {colors.get('action_bar_bg', colors['bg_panel'])};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            spacing: 8px;
            padding: 8px;
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
        /* Phase352: first-run and licensing identity surfaces. */
        QFrame#startupCard {{
            background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {colors.get('brand_gradient_start', colors['primary'])},
                stop:0.55 {colors.get('brand_gradient_mid', colors['primary_2'])},
                stop:1 {colors.get('brand_gradient_end', colors['accent'])});
            border: 1px solid rgba(255,255,255,0.24);
            border-radius: {radius_lg}px;
        }}
        QFrame#loginCard {{
            background-color: {colors.get('login_card_bg', colors['card_bg'])};
            border: 1px solid {colors['border']};
            border-radius: {radius_lg}px;
        }}
        QFrame#activationCard {{
            background-color: {colors.get('activation_card_bg', colors['card_bg'])};
            border: 1px solid {colors['border']};
            border-radius: {radius_lg}px;
        }}
        QFrame#brandCard {{
            background-color: {colors.get('surface_raised', colors['card_bg'])};
            border: 1px solid {colors['border']};
            border-radius: {radius_lg}px;
        }}
        QLabel#brandMark {{
            background-color: {colors.get('brand_mark_bg', colors['brand_soft'])};
            border: 1px solid {colors['border']};
            border-radius: {radius_lg}px;
            padding: 8px;
        }}
        QLabel#licenseStatusBadge {{
            background-color: {colors.get('license_status_bg', colors['info_soft'])};
            color: {colors['info']};
            border: 1px solid {colors['info']};
            border-radius: 14px;
            padding: 6px 12px;
            font-weight: 900;
        }}
        /* Phase353: branded first-run split panels and runtime polish. */
        QFrame#firstRunBrandPanel {{
            background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {colors.get('brand_gradient_start', colors['primary'])},
                stop:0.54 {colors.get('brand_gradient_mid', colors['primary_2'])},
                stop:1 {colors.get('brand_gradient_end', colors['accent'])});
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: {radius_lg}px;
        }}
        QFrame#firstRunFormPanel {{
            background-color: {colors.get('first_run_form_bg', colors.get('login_card_bg', colors['card_bg']))};
            border: 1px solid {colors.get('first_run_card_border', colors['border'])};
            border-radius: {radius_lg}px;
        }}
        /* Phase358: stable centered login layout, no split overlap. */
        QFrame#firstRunLoginHeader {{
            background-color: {colors.get('first_run_login_header_bg', colors.get('first_run_form_bg', colors['card_bg']))};
            border: 1px solid {colors.get('first_run_card_border', colors['border'])};
            border-radius: {radius_lg}px;
            min-height: 112px;
        }}
        QLabel#firstRunLoginLogo {{
            background-color: {colors.get('brand_mark_bg', colors['brand_soft'])};
            border: 1px solid {colors.get('first_run_card_border', colors['border'])};
            border-radius: {radius_md}px;
            padding: 6px;
        }}
        QLabel#firstRunLoginTitle {{
            color: {colors['text_primary']};
            font-size: {title_px}px;
            font-weight: 900;
        }}
        QLabel#firstRunLoginSubtitle {{
            color: {colors['text_secondary']};
            font-size: {value_px}px;
            line-height: 145%;
        }}
        QLabel#firstRunLoginModeChip {{
            background-color: {colors.get('info_soft', colors['brand_soft'])};
            color: {colors['info']};
            border: 1px solid {colors['info']};
            border-radius: 13px;
            padding: 5px 10px;
            font-weight: 800;
            min-height: 26px;
        }}
        QFrame#loginOptionsPanel {{
            background-color: {colors.get('surface_sunken', colors['bg_sidebar'])};
            border: 1px solid {colors.get('first_run_card_border', colors['border'])};
            border-radius: {radius_md}px;
        }}
        /* Phase360: RTL-first organized login screen sections. */
        QFrame#loginCredentialsPanel {{
            background-color: {colors.get('surface_raised', colors.get('first_run_form_bg', colors['card_bg']))};
            border: 1px solid {colors.get('first_run_card_border', colors['border'])};
            border-radius: {radius_md}px;
        }}
        QFrame#loginActionsPanel {{
            background-color: transparent;
            border: none;
        }}
        QLabel#loginFieldLabel {{
            color: {colors['text_primary']};
            font-size: {caption_px + 2}px;
            font-weight: 900;
            padding: 0 2px;
        }}
        QComboBox#loginUsernameField, QComboBox#loginLanguageField, QLineEdit#loginPasswordField {{
            min-height: 42px;
            border-radius: {radius_md}px;
            padding-left: 12px;
            padding-right: 12px;
        }}
        QPushButton#loginPasswordToggleButton {{
            background-color: {colors.get('bg_panel', colors['card_bg'])};
            color: {colors['primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
        }}
        QPushButton#loginPasswordToggleButton:hover {{
            background-color: {colors['brand_soft']};
        }}
        QFrame#loginCard[loginLayoutPolicy="pre352_rtl_ordered_no_overlay"] {{
            min-width: 430px;
        }}
        QFrame#loginCard[loginLayout="rtl_organized_split"] QFrame#firstRunFormPanel {{
            min-width: {BRAND.get('first_run_form_width', 520)}px;
        }}
        QFrame#loginCard[loginLayout="rtl_organized_split"] QFrame#firstRunBrandPanel {{
            min-width: {BRAND.get('first_run_panel_width', 330)}px;
            max-width: {BRAND.get('first_run_panel_width', 330)}px;
        }}
        QFrame#loginSeparator {{
            background-color: {colors.get('first_run_card_border', colors['border'])};
            border: none;
        }}
        QComboBox#loginUsernameCombo, QComboBox#loginLanguageCombo, QLineEdit#loginPasswordEdit {{
            min-height: 42px;
            border-radius: {radius_md}px;
            padding: 0 12px;
        }}
        QPushButton#loginPasswordVisibilityButton {{
            background-color: {colors.get('first_run_secondary_bg', colors['bg_panel'])};
            color: {colors['primary']};
            border: 1px solid {colors.get('first_run_card_border', colors['border'])};
            border-radius: {radius_md}px;
            min-width: 42px;
            max-width: 42px;
            min-height: 42px;
            max-height: 42px;
            padding: 0px;
            margin: 0px;
        }}
        QPushButton#loginPasswordVisibilityButton:checked {{
            background-color: {colors.get('first_run_primary_soft_bg', colors.get('selection_bg', colors['primary']))};
            border-color: {colors['primary']};
        }}
        QLabel#loginAdminWarning {{
            color: {colors['warning']};
            font-size: {caption_px + 1}px;
            font-weight: 700;
        }}
        QLabel#loginFooter {{
            color: {colors['text_muted']};
            font-size: {caption_px}px;
            font-weight: 700;
        }}
        /* Phase361/362/363/364: expanded vertical login layout; password/options sections never overlap. */
        QFrame#loginCard[loginOverlapPolicy="sectioned_no_overlap"] QFrame#loginCredentialsPanel {{
            margin-bottom: {BRAND.get('login_section_gap', 14)}px;
        }}
        QFrame#loginCard[loginOverlapPolicy="sectioned_no_overlap"] QFrame#loginOptionsPanel {{
            margin-top: 0px;
        }}

        QFrame#loginCard[loginSpacingPolicy="password_options_gap"] QFrame#loginCredentialsPanel {{
            margin-bottom: {BRAND.get('login_section_gap', 30)}px;
        }}
        QFrame#loginCard[loginSpacingPolicy="password_options_gap"] QLineEdit#loginPasswordEdit {{
            margin-bottom: {BRAND.get('login_password_bottom_gap', 18)}px;
        }}
        QFrame#loginPasswordRow {{
            background-color: transparent;
            border: none;
            min-height: {BRAND.get('login_password_row_height', 68)}px;
            max-height: {BRAND.get('login_password_row_height', 68)}px;
            margin: 0px;
            padding: 0px;
        }}
        QFrame#loginPasswordSafeSpacer {{
            background-color: transparent;
            border: none;
            min-height: {BRAND.get('login_password_options_spacer_height', 46)}px;
            max-height: {BRAND.get('login_password_options_spacer_height', 46)}px;
            margin: 0px;
            padding: 0px;
        }}
        QFrame#loginCard[loginSpacingPolicy="password_row_reserved_gap"] QFrame#loginCredentialsPanel {{
            margin-bottom: 0px;
        }}
        QFrame#loginCard[loginSpacingPolicy="password_row_reserved_gap"] QFrame#loginPasswordRow {{
            min-height: {BRAND.get('login_password_row_height', 68)}px;
            max-height: {BRAND.get('login_password_row_height', 68)}px;
        }}
        QFrame#loginCard[loginSpacingPolicy="password_row_reserved_gap"] QFrame#loginPasswordSafeSpacer {{
            min-height: {BRAND.get('login_password_options_spacer_height', 46)}px;
            max-height: {BRAND.get('login_password_options_spacer_height', 46)}px;
        }}
        QFrame#loginCard[loginDensity="expanded_vertical"] QFrame#firstRunFormPanel {{
            min-width: {BRAND.get('login_form_expanded_width', BRAND.get('first_run_form_width', 520))}px;
            min-height: {BRAND.get('login_form_expanded_min_height', 670)}px;
        }}
        QFrame#loginCard[loginDensity="expanded_vertical"] QFrame#loginCredentialsPanel {{
            min-height: {BRAND.get('login_credentials_min_height', 188)}px;
        }}
        QFrame#loginCard[loginDensity="expanded_vertical"] QFrame#loginOptionsPanel {{
            min-height: {BRAND.get('login_options_min_height', 98)}px;
        }}
        QFrame#loginCard[loginDensity="expanded_vertical"] QComboBox#loginUsernameCombo,
        QFrame#loginCard[loginDensity="expanded_vertical"] QComboBox#loginLanguageCombo,
        QFrame#loginCard[loginDensity="expanded_vertical"] QLineEdit#loginPasswordEdit {{
            min-height: {BRAND.get('login_field_height', 48)}px;
            padding-left: 14px;
            padding-right: 14px;
        }}
        QFrame#loginCard[loginDensity="expanded_vertical"] QPushButton#firstRunPrimary {{
            min-height: {BRAND.get('login_action_button_height', BRAND.get('first_run_primary_button_height', brand_button_min))}px;
        }}
        QFrame#loginCard[loginDensity="expanded_vertical"] QPushButton#firstRunSecondary {{
            min-height: {BRAND.get('login_secondary_button_height', BRAND.get('first_run_secondary_button_height', brand_button_min))}px;
        }}


        /* Phase431: horizontal branded login layout; wide brand panel + focused form panel. */
        QFrame#loginCard[loginLayout="horizontal_branded_split"] QFrame#firstRunBrandPanel {{
            min-width: {BRAND.get('login_horizontal_brand_width', BRAND.get('first_run_panel_width', 390))}px;
            max-width: {BRAND.get('login_horizontal_brand_width', BRAND.get('first_run_panel_width', 390))}px;
            min-height: {BRAND.get('login_horizontal_panel_min_height', 540)}px;
        }}
        QFrame#loginCard[loginLayout="horizontal_branded_split"] QFrame#firstRunFormPanel {{
            min-width: {BRAND.get('login_horizontal_form_width', BRAND.get('first_run_form_width', 610))}px;
            min-height: {BRAND.get('login_horizontal_panel_min_height', 540)}px;
        }}
        QFrame#loginCard[loginDensity="horizontal_compact"] QFrame#loginCredentialsPanel {{
            min-height: 180px;
            margin-bottom: 0px;
        }}
        QFrame#loginCard[loginDensity="horizontal_compact"] QFrame#loginOptionsPanel {{
            min-height: {BRAND.get('login_options_runtime_height', 54)}px;
            max-height: {BRAND.get('login_options_runtime_max_height', 62)}px;
        }}
        QFrame#loginCard[loginDensity="horizontal_compact"] QFrame#loginPasswordRow {{
            min-height: 50px;
            max-height: 54px;
        }}
        QFrame#loginCard[loginLayoutPolicy="horizontal_brand_form_no_overlay"] QLabel#firstRunFormTitle {{
            font-size: {title_px + 2}px;
        }}

        /* Phase432: runtime-stabilized horizontal login chrome and no-overlap fields. */
        QFrame#loginCard[loginRuntimePolicy="horizontal_runtime_stabilized"] QFrame#LoginRuntimeTitleBar {{
            min-height: {BRAND.get('login_runtime_titlebar_height', 40)}px;
            max-height: {BRAND.get('login_runtime_titlebar_height', 40)}px;
            background-color: {colors.get('first_run_form_bg', colors.get('login_card_bg', colors['card_bg']))};
            border-bottom: 1px solid {colors.get('first_run_card_border', colors['border'])};
            border-top-left-radius: {BRAND.get('basit_startup_card_radius', radius_lg)}px;
            border-top-right-radius: {BRAND.get('basit_startup_card_radius', radius_lg)}px;
        }}
        QLabel#LoginRuntimeTitle {{
            color: {colors['text_primary']};
            font-size: {value_px}px;
            font-weight: 900;
            background: transparent;
            border: none;
            padding: 0px;
        }}
        QPushButton#LoginRuntimeCloseButton,
        QPushButton#LoginRuntimeMinButton {{
            min-width: 30px;
            max-width: 30px;
            min-height: 30px;
            max-height: 30px;
            border-radius: 8px;
            border: 1px solid {colors.get('first_run_card_border', colors['border'])};
            background-color: {colors.get('first_run_secondary_bg', colors['bg_panel'])};
            color: {colors['text_primary']};
            padding: 0px;
            margin: 0px;
        }}
        QPushButton#LoginRuntimeCloseButton:hover,
        QPushButton#LoginRuntimeMinButton:hover {{
            background-color: {colors.get('brand_soft', colors['bg_panel'])};
            border-color: {colors['primary']};
        }}
        QFrame#loginCard[loginRuntimePolicy="horizontal_runtime_stabilized"] QLabel#firstRunHeroTitle,
        QFrame#loginCard[loginRuntimePolicy="horizontal_runtime_stabilized"] QLabel#firstRunSubtitle,
        QFrame#loginCard[loginRuntimePolicy="horizontal_runtime_stabilized"] QLabel#firstRunFooter {{
            background: transparent;
            border: none;
            padding-left: 0px;
            padding-right: 0px;
        }}
        QFrame#loginCard[loginRuntimePolicy="horizontal_runtime_stabilized"] QFrame#loginCredentialsPanel {{
            min-height: 180px;
            max-height: 205px;
            background-color: {colors.get('surface_raised', colors['card_bg'])};
            border: 1px solid {colors.get('first_run_card_border', colors['border'])};
            border-radius: {radius_md}px;
        }}
        QFrame#loginCard[loginRuntimePolicy="horizontal_runtime_stabilized"] QFrame#loginOptionsPanel {{
            min-height: {BRAND.get('login_options_runtime_height', 54)}px;
            max-height: {BRAND.get('login_options_runtime_max_height', 62)}px;
            background-color: {colors.get('surface_raised', colors['card_bg'])};
            border: 1px solid {colors.get('first_run_card_border', colors['border'])};
            border-radius: {radius_md}px;
        }}
        QFrame#loginCard[loginRuntimePolicy="horizontal_runtime_stabilized"] QLabel#loginAdminWarning {{
            min-height: {BRAND.get('login_warning_reserved_height', 30)}px;
            max-height: {BRAND.get('login_warning_reserved_max_height', 40)}px;
            background-color: {colors.get('warning_soft', '#FFF6E0')};
            color: {colors.get('warning', '#B7791F')};
            border: 1px solid {colors.get('warning', '#B7791F')};
            border-radius: {radius_sm}px;
            padding: 4px 8px;
            font-weight: 800;
        }}
        QLabel#loginRuntimeMessage {{
            min-height: {BRAND.get('login_message_reserved_height', 34)}px;
            max-height: {BRAND.get('login_message_reserved_max_height', 44)}px;
            border-radius: {radius_sm}px;
            padding: 4px 8px;
            font-weight: 900;
            background: transparent;
            border: 1px solid transparent;
        }}
        QLabel#loginRuntimeMessage[messageState="danger"] {{
            background-color: {colors.get('danger', '#D92D20')};
            color: white;
            border-color: {colors.get('danger', '#D92D20')};
        }}
        QLabel#loginRuntimeMessage[messageState="success"] {{
            background-color: {colors.get('success_soft', '#E7F6EC')};
            color: {colors.get('success', '#0E8F5A')};
            border-color: {colors.get('success', '#0E8F5A')};
        }}

        /* Phase433: password row visible fix; options cannot consume or cover password input. */
        QFrame#loginCard[loginPasswordPolicy="password_row_visible_fixed"] QFrame#loginCredentialsPanel {{
            min-height: {BRAND.get('login_credentials_runtime_fixed_height', 246)}px;
            max-height: {BRAND.get('login_credentials_runtime_max_height', 278)}px;
        }}
        QFrame#loginCard[loginPasswordPolicy="password_row_visible_fixed"] QFrame#loginPasswordRow {{
            min-height: {BRAND.get('login_password_runtime_row_height', 58)}px;
            max-height: {BRAND.get('login_password_runtime_row_max_height', 64)}px;
            background: transparent;
            border: none;
            margin: 0px;
            padding: 0px;
        }}
        QFrame#loginCard[loginPasswordPolicy="password_row_visible_fixed"] QLineEdit#loginPasswordEdit {{
            min-height: {BRAND.get('login_password_runtime_field_height', BRAND.get('login_field_height', 46))}px;
            max-height: {BRAND.get('login_password_runtime_field_max_height', BRAND.get('login_field_height', 52))}px;
            background-color: {colors.get('input_bg', colors.get('card_bg', '#FFFFFF'))};
            border: 1px solid {colors.get('border', '#D0D7DE')};
            border-radius: {radius_md}px;
            padding-left: 12px;
            padding-right: 12px;
        }}
        QFrame#loginCard[loginPasswordPolicy="password_row_visible_fixed"] QPushButton#loginPasswordVisibilityButton {{
            min-width: {BRAND.get('login_password_runtime_button_size', 42)}px;
            max-width: {BRAND.get('login_password_runtime_button_size', 42)}px;
            min-height: {BRAND.get('login_password_runtime_button_size', 42)}px;
            max-height: {BRAND.get('login_password_runtime_button_size', 42)}px;
        }}
        QFrame#loginCard[loginPasswordPolicy="password_row_visible_fixed"] QFrame#loginOptionsPanel {{
            margin-top: 0px;
        }}

        QLabel#firstRunHeroTitle {{
            color: {colors.get('first_run_panel_text', '#FFFFFF')};
            font-size: {hero_px + 2}px;
            font-weight: 900;
            letter-spacing: 0.3px;
        }}
        QLabel#firstRunSubtitle {{
            color: {colors.get('first_run_panel_muted', 'rgba(255,255,255,0.76)')};
            font-size: {value_px}px;
            line-height: 150%;
        }}
        QLabel#firstRunChip, QLabel#firstRunStageChip {{
            background-color: {colors.get('first_run_chip_bg', 'rgba(255,255,255,0.16)')};
            color: {colors.get('first_run_chip_text', '#FFFFFF')};
            border: 1px solid rgba(255,255,255,0.20);
            border-radius: 14px;
            padding: 6px 11px;
            font-weight: 800;
            min-height: {BRAND.get('first_run_chip_height', 30)}px;
        }}
        QLabel#firstRunFooter {{
            color: {colors.get('first_run_footer_text', 'rgba(255,255,255,0.58)')};
            font-size: {caption_px}px;
            font-weight: 700;
        }}
        QLabel#firstRunFormTitle {{
            color: {colors['text_primary']};
            font-size: {title_px}px;
            font-weight: 900;
        }}
        QLabel#firstRunFormSubtitle {{
            color: {colors['text_secondary']};
            font-size: {value_px}px;
        }}
        QPushButton#firstRunPrimary {{
            background-color: {colors.get('first_run_primary_bg', colors['primary'])};
            color: white;
            border: none;
            border-radius: {radius_md}px;
            padding: 11px 22px;
            font-size: {value_px + 1}px;
            font-weight: 900;
            min-height: {BRAND.get('first_run_primary_button_height', brand_button_min)}px;
        }}
        QPushButton#firstRunPrimary:hover {{ background-color: {colors['primary_hover']}; }}
        QPushButton#firstRunSecondary {{
            background-color: {colors.get('first_run_secondary_bg', colors['bg_panel'])};
            color: {colors['primary']};
            border: 1px solid {colors['primary']};
            border-radius: {radius_md}px;
            padding: 9px 16px;
            font-weight: 900;
            min-height: {BRAND.get('first_run_secondary_button_height', brand_button_min)}px;
        }}
        QFrame#activationDevicePanel {{
            background-color: {colors.get('activation_device_bg', colors['info_soft'])};
            border: 1px solid {colors.get('first_run_card_border', colors['border'])};
            border-radius: {radius_md}px;
            min-height: {BRAND.get('first_run_device_panel_height', 92)}px;
        }}
        QLabel#activationDeviceTitle {{
            color: {colors['primary']};
            font-weight: 900;
            font-size: {value_px}px;
        }}
        QLabel#activationDeviceLine {{
            color: {colors['text_secondary']};
            font-size: {caption_px + 1}px;
        }}
        QProgressBar#firstRunProgressTrack {{
            background-color: {colors.get('splash_progress_bg', 'rgba(255,255,255,0.24)')};
            border: none;
            border-radius: 7px;
            min-height: 14px;
            color: white;
            font-weight: 800;
        }}
        QProgressBar#firstRunProgressTrack::chunk {{
            background-color: {colors.get('splash_progress_chunk', '#FFFFFF')};
            border-radius: 7px;
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

        /* Phase352: branded dialogs and system windows. */
        QDialog QFrame#dialogHeader, QFrame#DialogHeader {{
            min-height: {dialog_header_height}px;
            background-color: {colors.get('dialog_header_bg', colors['brand_soft'])};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
        }}
        QDialog QWidget#dialogFooter, QFrame#DialogFooter {{
            background-color: {colors.get('dialog_footer_bg', colors['bg_window'])};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 8px;
        }}
        QMessageBox, QFileDialog, QColorDialog {{
            background-color: {colors.get('dialog_bg', colors['bg_panel'])};
            color: {colors['text_primary']};
        }}
        QDialog QPushButton, QMessageBox QPushButton {{
            min-height: {brand_button_min}px;
            padding: 9px 18px;
            font-weight: 900;
        }}


        /* Phase349: unified invoice-like footer summary and bottom actions. */
        QFrame#TransactionFooterPanel {{
            background-color: {colors['bg_panel']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 6px;
        }}
        QFrame#TransactionHorizontalSummaryFrame,
        QFrame#TransactionHorizontalPaymentFrame {{
            background-color: {colors.get('transaction_summary_bg', colors['card_bg'])};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 4px;
            min-height: 68px;
        }}
        QLabel#TransactionSummaryCaption,
        QLabel#TransactionPaymentCaption {{
            color: {colors['text_secondary']};
            font-size: {footer_px}px;
            font-weight: 800;
        }}
        QLabel#TransactionSummaryValue {{
            color: {colors.get('transaction_summary_value', colors['primary'])};
            font-size: {footer_value_px}px;
            font-weight: 900;
            min-width: 72px;
        }}
        QFrame#TransactionHorizontalPaymentFrame QComboBox,
        QFrame#TransactionHorizontalPaymentFrame QDoubleSpinBox {{
            min-height: 36px;
            font-size: {footer_px}px;
            font-weight: 800;
        }}
        QPushButton#TransactionFooterMiniButton {{
            min-height: 36px;
            padding: 7px 12px;
            font-size: {footer_px}px;
            font-weight: 900;
            border-radius: {radius_sm}px;
        }}
        QWidget#TransactionBottomActionBar {{
            background-color: {colors['bg_panel']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            padding: 8px;
        }}
        QWidget#TransactionBottomActionBar QPushButton {{
            min-height: {footer_action_min}px;
            padding: 10px 18px;
            font-size: {footer_action_px}px;
            font-weight: 900;
            border-radius: {radius_md}px;
        }}
        QWidget#TransactionBottomActionBar QPushButton[transaction_action="save"],
        QWidget#TransactionBottomActionBar QPushButton[transaction_action="print"],
        QWidget#TransactionBottomActionBar QPushButton[transaction_action="update"] {{
            background-color: {colors.get('transaction_action_bg', colors['primary'])};
            color: white;
            border-color: {colors.get('transaction_action_bg', colors['primary'])};
        }}
        QWidget#TransactionBottomActionBar QPushButton[transaction_action="delete"] {{
            background-color: {colors['danger_soft']};
            color: {colors['danger']};
            border-color: {colors['danger']};
        }}


        /* Phase355: branded table surface and active editable cell. */
        QTableView[brand_table_surface="true"],
        QTableWidget[brand_table_surface="true"],
        QTreeView[brand_table_surface="true"] {{
            background-color: {colors.get('bg_table', colors['bg_panel'])};
            alternate-background-color: {colors.get('bg_table_alt', colors['surface_sunken'])};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            gridline-color: {colors['border']};
            selection-background-color: {colors['selection_bg']};
            selection-color: {colors['selection_text']};
        }}
        QTableView[brand_table_surface="true"]::item,
        QTableWidget[brand_table_surface="true"]::item,
        QTreeView[brand_table_surface="true"]::item {{
            min-height: {brand_table_row_height}px;
            padding: {table_cell_padding + 1}px {table_cell_padding + 3}px;
        }}
        QTableView[brand_table_surface="true"]::item:hover,
        QTableWidget[brand_table_surface="true"]::item:hover {{
            background-color: {colors.get('table_row_hover_bg', colors['brand_soft'])};
        }}
        QTableView[brand_entry_table="true"]::item:focus,
        QTableWidget[brand_entry_table="true"]::item:focus,
        QTableView[standard_table_keyboard="true"]::item:focus,
        QTableWidget[standard_table_keyboard="true"]::item:focus,
        QTableView[current_cell_highlight="true"]::item:focus,
        QTableWidget[current_cell_highlight="true"]::item:focus,
        QTableView#TransactionLineGrid::item:focus {{
            background-color: {colors.get('table_current_bg', colors.get('current_cell_bg', colors['warning_soft']))};
            color: {colors.get('table_current_text', colors['text_primary'])};
            border: {brand_table_current_border}px solid {colors.get('table_current_border', colors.get('current_cell_border', colors['primary']))};
            font-weight: 900;
        }}
        QTableView[brand_entry_table="true"] QLineEdit:focus,
        QTableWidget[brand_entry_table="true"] QLineEdit:focus,
        QTableView#TransactionLineGrid QLineEdit:focus {{
            background-color: {colors.get('table_current_bg', colors.get('current_cell_bg', colors['warning_soft']))};
            color: {colors.get('table_current_text', colors['text_primary'])};
            border: {brand_table_current_border}px solid {colors.get('table_focus_ring', colors['primary'])};
            selection-background-color: {colors['primary']};
            selection-color: white;
        }}
        QHeaderView::section {{
            min-height: {brand_table_header_min_height}px;
            border-bottom: 3px solid {colors.get('table_header_line', colors.get('brand_gold', colors['primary']))};
        }}

        /* Phase355: branded transaction footer and bottom commands. */
        QFrame#TransactionFooterPanel {{
            min-height: {transaction_footer_min}px;
            background-color: {colors.get('transaction_footer_surface', colors['bg_panel'])};
            border: 1px solid {colors.get('transaction_footer_summary_border', colors['border'])};
            border-radius: {radius_lg}px;
            padding: 8px;
        }}
        QFrame#TransactionHorizontalSummaryFrame,
        QFrame#TransactionHorizontalPaymentFrame {{
            min-height: {transaction_summary_min}px;
            background-color: {colors.get('transaction_footer_summary_bg', colors.get('transaction_summary_bg', colors['card_bg']))};
            border: 1px solid {colors.get('transaction_footer_summary_border', colors['border'])};
            border-radius: {radius_md}px;
            padding: 6px;
        }}
        QLabel#TransactionSummaryCaption,
        QLabel#TransactionPaymentCaption {{
            color: {colors.get('transaction_footer_label', colors['text_secondary'])};
            font-size: {footer_px}px;
            font-weight: 900;
            min-height: 18px;
        }}
        QLabel#TransactionSummaryValue {{
            color: {colors.get('transaction_footer_value', colors.get('transaction_summary_value', colors['primary']))};
            font-size: {footer_value_px + 1}px;
            font-weight: 950;
            min-width: 84px;
            min-height: 24px;
        }}
        QTextEdit#TransactionFooterNotes {{
            min-height: 72px;
            background-color: {colors.get('transaction_footer_summary_bg', colors.get('transaction_summary_bg', colors['card_bg']))};
            border: 1px solid {colors.get('transaction_footer_summary_border', colors['border'])};
            border-radius: {radius_md}px;
            font-size: {footer_px}px;
            padding: 8px;
        }}
        QWidget#TransactionBottomActionBar QPushButton {{
            min-height: {footer_action_min + 4}px;
            min-width: {transaction_button_min_width}px;
            padding: 11px 20px;
            font-size: {footer_action_px + 1}px;
            font-weight: 950;
            border-radius: {radius_md}px;
        }}
        QWidget#TransactionBottomActionBar QPushButton[transaction_action="save"],
        QWidget#TransactionBottomActionBar QPushButton[transaction_action="print"],
        QWidget#TransactionBottomActionBar QPushButton[transaction_action="update"] {{
            background-color: {colors.get('transaction_footer_primary_bg', colors.get('transaction_action_bg', colors['primary']))};
            color: white;
            border-color: {colors.get('transaction_footer_primary_bg', colors.get('transaction_action_bg', colors['primary']))};
        }}
        QWidget#TransactionBottomActionBar QPushButton[transaction_action="close"],
        QWidget#TransactionBottomActionBar QPushButton[transaction_action="create"] {{
            background-color: {colors.get('transaction_footer_secondary_bg', colors.get('transaction_close_bg', colors['bg_panel']))};
            color: {colors['text_primary']};
            border-color: {colors.get('transaction_footer_summary_border', colors['border'])};
        }}

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

        /* Phase428/430: shared Restaurant/Cafe operational material card grid; POS is barcode/table-first. */
        QWidget#operationalItemCardGrid,
        QWidget#restaurantMenuOperationalItemCardGrid,
        QWidget#restaurantSimpleItemCardGrid {{
            background-color: {colors['bg_table']};
        }}
        QScrollArea#operationalItemCardScroll {{
            background-color: {colors['bg_table']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
        }}
        QWidget#operationalItemCardHost {{
            background-color: {colors['bg_table']};
        }}
        QPushButton#operationalItemCardButton {{
            background-color: {colors['card_bg']};
            color: {colors['text_primary']};
            border: 2px solid {colors['border']};
            border-radius: {radius_lg}px;
            padding: 8px 10px;
            font-size: {value_px}px;
            font-weight: 900;
            text-align: center;
        }}
        QPushButton#operationalItemCardButton:hover {{
            background-color: {colors['brand_soft']};
            color: {colors['primary']};
            border-color: {colors['primary']};
        }}
        QLabel#operationalItemCardEmpty {{
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


        /* Phase354: branded workspace tab cards.  Runtime labels include
           a visible main/sub badge text; these selectors provide the identity
           surface for both QTabWidget and TabbedWorkspace. */
        QTabWidget#TabbedWorkspace::pane {{
            border: 1px solid {colors['border']};
            border-top: none;
            background-color: {colors.get('surface_root', colors['bg_window'])};
            border-radius: {radius_lg}px;
        }}
        QTabWidget#TabbedWorkspace QTabBar::tab,
        QTabBar::tab[tabKind="main"],
        QTabBar::tab[tabKind="sub"] {{
            min-height: {BRAND.get('brand_tab_min_height', 38)}px;
            min-width: {BRAND.get('shell_tab_active_min_width', 150)}px;
            padding: 8px {BRAND.get('brand_tab_padding_x', 18)}px;
            margin-left: 4px;
            border: 1px solid {colors['border']};
            border-top-left-radius: {radius_md}px;
            border-top-right-radius: {radius_md}px;
            background-color: {colors.get('tab_inactive_bg', colors['bg_panel'])};
            color: {colors.get('tab_inactive_text', colors['text_secondary'])};
            font-weight: 900;
        }}
        QTabWidget#TabbedWorkspace QTabBar::tab:selected {{
            background-color: {colors.get('tab_active_bg', colors['primary'])};
            color: {colors.get('tab_active_text', '#FFFFFF')};
            border-color: {colors.get('tab_active_bg', colors['primary'])};
            border-bottom: 4px solid {colors.get('shell_tab_active_underline', colors['accent'])};
        }}
        QTabWidget#TabbedWorkspace QTabBar::tab:hover:!selected {{
            background-color: {colors.get('brand_soft', colors['bg_table_alt'])};
            color: {colors['primary']};
            border-color: {colors['primary']};
        }}

        /* Phase354: branded icon menu and action bar runtime. */
        QFrame#CleanShellNavigationBar {{
            background-color: {colors.get('menu_bg', colors['bg_panel'])};
            border-bottom: 1px solid {colors.get('menu_border', colors['border'])};
        }}
        QPushButton#MainNavButton {{
            border-radius: {BRAND.get('shell_menu_button_radius', 16)}px;
            font-weight: 950;
        }}
        QPushButton#MainNavButton:hover {{
            background-color: {colors.get('shell_menu_hover_bg', colors.get('brand_soft', colors['bg_table_alt']))};
            color: {colors['primary']};
            border-color: {colors['primary']};
        }}
        QFrame#UnifiedActionBar {{
            background-color: {colors.get('action_bar_bg', colors['bg_panel'])};
            border-bottom: 1px solid {colors['border']};
        }}
        QLabel#ActionBarContext {{
            background-color: {colors.get('shell_action_context_bg', colors['bg_panel'])};
            color: {colors['primary']};
            border: 1px solid {colors['border']};
            border-radius: {radius_md}px;
            min-width: {BRAND.get('shell_action_context_min_width', 180)}px;
            padding: 7px 12px;
            font-weight: 950;
        }}
        QFrame#UnifiedActionBar QToolButton[shellChromeRole="primary"] {{
            background-color: {colors.get('shell_action_primary_bg', colors['primary'])};
            color: white;
            border-color: {colors.get('shell_action_primary_bg', colors['primary'])};
            min-width: {BRAND.get('shell_action_primary_min_width', 112)}px;
            font-weight: 950;
        }}
        QFrame#UnifiedActionBar QToolButton[shellChromeRole="secondary"] {{
            background-color: {colors.get('shell_action_secondary_bg', colors['bg_panel'])};
        }}
        QFrame#UnifiedActionBar QToolButton[shellChromeRole="utility"],
        QLabel#ActionBarUserLabel[shellChromeRole="user"] {{
            background-color: {colors.get('shell_action_utility_bg', colors['bg_panel'])};
            color: {colors['text_secondary']};
        }}





        /* Phase446: project-wide shell header and action bar consolidation. */
        QFrame#CleanShellNavigationBar[projectVisualIdentityPhase="446"] {{
            background-color: {colors.get('shell_navigation_bg', colors.get('menu_bg', colors['bg_panel']))};
            border-bottom: 1px solid {colors.get('shell_navigation_border', colors['border'])};
        }}
        QPushButton#MainNavButton[projectVisualIdentityPhase="446"] {{
            background-color: {colors.get('shell_navigation_button_bg', colors['bg_panel'])};
            color: {colors.get('shell_navigation_button_text', colors['text_primary'])};
            border: 1px solid {colors.get('shell_navigation_button_border', colors['border'])};
            border-bottom: 3px solid transparent;
            border-radius: {radius_md}px;
            font-weight: 850;
        }}
        QPushButton#MainNavButton[projectVisualIdentityPhase="446"]:hover {{
            background-color: {colors.get('shell_navigation_button_hover_bg', colors.get('brand_soft', colors['bg_table_alt']))};
            color: {colors.get('shell_navigation_button_hover_text', colors['primary'])};
            border-color: {colors.get('shell_navigation_active_indicator', colors.get('accent', colors['primary']))};
            border-bottom-color: {colors.get('shell_navigation_active_indicator', colors.get('accent', colors['primary']))};
        }}
        QFrame#UnifiedActionBar[projectVisualIdentityPhase="446"] {{
            background-color: {colors.get('shell_action_bar_bg', colors.get('action_bar_bg', colors['bg_panel']))};
            border-bottom: 1px solid {colors.get('shell_action_bar_border', colors['border'])};
        }}
        QFrame#UnifiedActionBar[projectVisualIdentityPhase="446"] QToolButton {{
            border-radius: {radius_md}px;
            font-weight: 800;
        }}

        /* Phase407: Basit-inspired startup, login, activation and dialogs. */
        QFrame#startupCard[basitStartupSurface="true"] {{
            background-color: {colors.get('basit_blue', colors['primary'])};
            border: 3px solid {colors.get('basit_yellow', colors['warning'])};
            border-radius: {BRAND.get('basit_startup_card_radius', radius_lg)}px;
        }}
        QFrame#startupCard[basitStartupSurface="true"] QLabel#brandMark {{
            background-color: {colors.get('basit_yellow', colors['warning'])};
            border: 2px solid {colors.get('basit_red', colors['danger'])};
            border-radius: {radius_sm}px;
        }}
        QFrame#startupCard[basitStartupSurface="true"] QLabel#firstRunStageChip,
        QFrame#startupCard[basitStartupSurface="true"] QLabel[firstRunStageChip="true"] {{
            background-color: {colors.get('basit_table_bg', colors['bg_panel'])};
            color: {colors.get('basit_shell_active_text', colors['text_primary'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 3px;
            padding: 5px 10px;
            font-weight: 900;
        }}
        QFrame#loginCard[basitFirstRunChrome="true"],
        QFrame#activationCard[basitFirstRunChrome="true"] {{
            background-color: {colors.get('basit_canvas', colors['bg_window'])};
            border: 2px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-top: 5px solid {colors.get('basit_yellow', colors['warning'])};
            border-radius: {BRAND.get('basit_startup_card_radius', radius_lg)}px;
        }}
        QFrame#loginCard[basitFirstRunChrome="true"] QLabel#heroTitle,
        QFrame#activationCard[basitFirstRunChrome="true"] QLabel#firstRunFormTitle {{
            color: {colors.get('basit_blue', colors['primary'])};
            background-color: {colors.get('basit_yellow', colors['warning'])};
            border: 1px solid {colors.get('basit_red', colors['danger'])};
            border-radius: 3px;
            padding: 8px 12px;
            font-weight: 950;
        }}
        QFrame#loginCard[basitFirstRunChrome="true"] QLineEdit,
        QFrame#loginCard[basitFirstRunChrome="true"] QComboBox,
        QFrame#activationCard[basitFirstRunChrome="true"] QLineEdit,
        QDialog[basitDialogSurface="true"] QLineEdit,
        QDialog[basitDialogSurface="true"] QComboBox {{
            background-color: {colors.get('basit_table_bg', colors['bg_panel'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-right: 4px solid {colors.get('basit_blue', colors['primary'])};
            border-radius: 3px;
            min-height: {BRAND.get('basit_dialog_button_height', input_min)}px;
            font-weight: 800;
        }}
        QFrame#loginCard[basitFirstRunChrome="true"] QPushButton#primary,
        QFrame#activationCard[basitFirstRunChrome="true"] QPushButton#firstRunPrimary,
        QDialog[basitDialogSurface="true"] QPushButton[dialogActionRole="primary"] {{
            background-color: {colors.get('basit_blue', colors['primary'])};
            color: {colors.get('basit_card_text', '#FFFFFF')};
            border: 2px solid {colors.get('basit_card_border', colors['primary'])};
            border-bottom: 4px solid {colors.get('basit_yellow', colors['warning'])};
            border-radius: 3px;
            min-height: {BRAND.get('basit_dialog_button_height', 44)}px;
            font-weight: 950;
        }}
        QFrame#loginCard[basitFirstRunChrome="true"] QPushButton#primary:hover,
        QFrame#activationCard[basitFirstRunChrome="true"] QPushButton#firstRunPrimary:hover,
        QDialog[basitDialogSurface="true"] QPushButton[dialogActionRole="primary"]:hover {{
            background-color: {colors.get('basit_blue_hover', colors.get('primary_hover', colors['primary']))};
            border-color: {colors.get('basit_yellow', colors['warning'])};
        }}
        QFrame#loginCard[basitFirstRunChrome="true"] QPushButton#secondary,
        QFrame#activationCard[basitFirstRunChrome="true"] QPushButton#firstRunSecondary,
        QDialog[basitDialogSurface="true"] QPushButton[dialogActionRole="secondary"],
        QDialog[basitDialogSurface="true"] QPushButton[dialogActionRole="close"] {{
            background-color: {colors.get('basit_table_bg', colors['bg_panel'])};
            color: {colors.get('basit_shell_active_text', colors['text_primary'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 3px;
            min-height: {BRAND.get('basit_dialog_button_height', 44)}px;
            font-weight: 900;
        }}
        QFrame#loginCard[basitFirstRunChrome="true"] QLabel#danger,
        QDialog[basitDialogSurface="true"] QLabel#danger {{
            background-color: {colors.get('basit_red', colors['danger'])};
            color: {colors.get('basit_total_text', '#FFFFFF')};
            border-radius: 3px;
            padding: 6px 10px;
            font-weight: 900;
        }}
        QDialog[basitDialogSurface="true"] QFrame#BrandDialogFrame,
        QMessageBox[basitDialogSurface="true"] {{
            background-color: {colors.get('basit_canvas', colors['bg_window'])};
            border: 2px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-top: 5px solid {colors.get('basit_yellow', colors['warning'])};
            border-radius: {BRAND.get('basit_startup_card_radius', radius_lg)}px;
        }}
        QDialog[basitDialogSurface="true"] QFrame#BrandDialogHeader {{
            min-height: {BRAND.get('basit_dialog_header_height', dialog_header_height)}px;
            background-color: {colors.get('basit_blue', colors['primary'])};
            color: {colors.get('basit_card_text', '#FFFFFF')};
            border-bottom: 4px solid {colors.get('basit_yellow', colors['warning'])};
            border-top-left-radius: {BRAND.get('basit_startup_card_radius', radius_lg)}px;
            border-top-right-radius: {BRAND.get('basit_startup_card_radius', radius_lg)}px;
        }}
        QDialog[basitDialogSurface="true"] QLabel#BrandDialogTitle {{
            color: {colors.get('basit_card_text', '#FFFFFF')};
            font-weight: 950;
        }}

        /* Phase356: branded dialogs and system windows. */
        QDialog[brandDialog="true"], QMessageBox[brandDialog="true"] {{
            background-color: {colors.get('dialog_overlay_bg', colors.get('surface_root', colors['bg_window']))};
            color: {colors['text_primary']};
            border-radius: {radius_lg}px;
        }}
        QFrame#BrandDialogFrame {{
            background-color: {colors.get('dialog_bg', colors['bg_panel'])};
            border: 1px solid {colors.get('dialog_panel_border', colors['border'])};
            border-radius: {radius_lg}px;
        }}
        QFrame#BrandDialogHeader {{
            min-height: {dialog_header_height}px;
            background-color: {colors.get('brand_navy', colors['primary'])};
            color: {colors.get('dialog_header_text', '#FFFFFF')};
            border-top-left-radius: {radius_lg}px;
            border-top-right-radius: {radius_lg}px;
            border-bottom: 3px solid {colors.get('dialog_accent_line', colors.get('brand_gold', colors['warning']))};
        }}
        QLabel#BrandDialogTitle {{
            color: {colors.get('dialog_header_text', '#FFFFFF')};
            font-size: {title_px}px;
            font-weight: 950;
            background: transparent;
        }}
        QWidget[dialogSurface="body"] {{
            background-color: {colors.get('dialog_bg', colors['bg_panel'])};
            color: {colors['text_primary']};
            border-bottom-left-radius: {radius_lg}px;
            border-bottom-right-radius: {radius_lg}px;
        }}
        QWidget[dialogSurface="footer"], QDialogButtonBox[dialogSurface="footer"] {{
            background-color: {colors.get('dialog_footer_bg', colors['bg_window'])};
            border-top: 1px solid {colors['border']};
            padding: 10px;
        }}
        QFrame#ModernPageHeader[dialogSurface="headerCard"], QFrame#BrandDialogHeaderCard {{
            background-color: {colors.get('dialog_header_bg', colors['brand_soft'])};
            border: 1px solid {colors.get('dialog_panel_border', colors['border'])};
            border-right: 5px solid {colors.get('dialog_accent_line', colors.get('brand_gold', colors['warning']))};
            border-radius: {radius_md}px;
        }}
        QDialog[brandDialog="true"] QLabel#ModernPageTitle,
        QDialog[brandDialog="true"] QLabel[dialogLabelRole="title"] {{
            color: {colors.get('dialog_title_text', colors['primary'])};
            font-size: {title_px}px;
            font-weight: 950;
        }}
        QDialog[brandDialog="true"] QLabel#ModernPageSubtitle,
        QDialog[brandDialog="true"] QLabel[dialogLabelRole="subtitle"] {{
            color: {colors.get('dialog_subtitle_text', colors['text_secondary'])};
            font-size: {caption_px + 1}px;
        }}
        QDialog[brandDialog="true"] QPushButton,
        QMessageBox[brandDialog="true"] QPushButton {{
            min-height: {BRAND.get('dialog_action_min_height', 42)}px;
            min-width: {BRAND.get('dialog_action_min_width', 104)}px;
            border-radius: {radius_md}px;
            font-size: {action_px}px;
            font-weight: 900;
            padding: 8px 16px;
        }}
        QPushButton[dialogActionRole="primary"] {{
            background-color: {colors.get('dialog_primary_bg', colors['primary'])};
            color: white;
            border: 1px solid {colors.get('dialog_primary_bg', colors['primary'])};
            min-width: {BRAND.get('dialog_primary_min_width', 126)}px;
        }}
        QPushButton[dialogActionRole="primary"]:hover {{
            background-color: {colors['primary_hover']};
            border-color: {colors['primary_hover']};
        }}
        QPushButton[dialogActionRole="secondary"] {{
            background-color: {colors.get('dialog_secondary_bg', colors['bg_panel'])};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
        }}
        QPushButton[dialogActionRole="close"] {{
            background-color: {colors.get('dialog_close_bg', colors['bg_panel'])};
            color: {colors['text_secondary']};
            border: 1px solid {colors['border']};
        }}
        QPushButton[dialogActionRole="danger"] {{
            background-color: {colors.get('dialog_danger_bg', colors['danger_soft'])};
            color: {colors['danger']};
            border: 1px solid {colors['danger']};
        }}
        QMessageBox QLabel {{
            color: {colors['text_primary']};
            font-size: {value_px}px;
            font-weight: 750;
            padding: 8px;
        }}
        QMessageBox QLabel#qt_msgbox_label {{
            color: {colors['text_primary']};
        }}
        QMessageBox[dialogKind="message_warning"] {{
            background-color: {colors.get('dialog_warning_bg', colors['warning_soft'])};
        }}
        QMessageBox[dialogKind="message_error"] {{
            background-color: {colors.get('dialog_danger_bg', colors['danger_soft'])};
        }}
        QFrame#ToastNotification {{
            border-radius: {radius_md}px;
            border: 1px solid {colors['border']};
            border-right: 5px solid {colors.get('dialog_accent_line', colors['accent'])};
        }}
        QFrame#ToastNotification[toastType="success"] {{
            background-color: {colors.get('toast_success_bg', colors['success_soft'])};
            color: {colors.get('toast_success_text', colors['success'])};
        }}
        QFrame#ToastNotification[toastType="info"] {{
            background-color: {colors.get('toast_info_bg', colors['info_soft'])};
            color: {colors.get('toast_info_text', colors['info'])};
        }}
        QFrame#ToastNotification[toastType="warning"] {{
            background-color: {colors.get('toast_warning_bg', colors['warning_soft'])};
            color: {colors.get('toast_warning_text', colors['warning'])};
        }}
        QFrame#ToastNotification[toastType="error"] {{
            background-color: {colors.get('toast_error_bg', colors['danger_soft'])};
            color: {colors.get('toast_error_text', colors['danger'])};
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

        /* Phase401: Basit inspired operational skin. */
        QWidget[basitInspired="true"],
        QWidget#restaurantSimplePOSWidget {{
            background-color: {colors.get('basit_canvas', colors['bg_window'])};
        }}
        QWidget#restaurantSimplePOSWidget QLineEdit#restaurantSimpleSearch {{
            min-height: {BRAND.get('basit_toolbar_height', 46)}px;
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            background-color: #FFFFFF;
            color: {colors['text_primary']};
            font-weight: 800;
        }}
        QWidget#restaurantSimplePOSWidget QPushButton#restaurantSimpleSearchButton,
        QWidget#restaurantSimplePOSWidget QPushButton#restaurantSimpleNewSaleButton,
        QWidget#restaurantSimplePOSWidget QPushButton#restaurantSimpleRefreshButton,
        QWidget#restaurantSimplePOSWidget QPushButton#restaurantSimpleFullscreenButton {{
            min-height: {BRAND.get('basit_toolbar_height', 46)}px;
            background-color: {colors.get('basit_blue', colors['primary'])};
            color: #FFFFFF;
            border: 1px solid {colors.get('basit_card_border', colors['primary'])};
            border-radius: 4px;
            padding: 8px 14px;
            font-weight: 900;
        }}
        QWidget#restaurantSimplePOSWidget QPushButton#restaurantSimpleSearchButton:hover,
        QWidget#restaurantSimplePOSWidget QPushButton#restaurantSimpleNewSaleButton:hover,
        QWidget#restaurantSimplePOSWidget QPushButton#restaurantSimpleRefreshButton:hover,
        QWidget#restaurantSimplePOSWidget QPushButton#restaurantSimpleFullscreenButton:hover {{
            background-color: {colors.get('basit_blue_hover', colors['primary_hover'])};
        }}
        QFrame#restaurantSimpleSection {{
            background-color: {colors.get('basit_table_bg', colors['bg_panel'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
        }}
        QLabel#restaurantSimpleSectionTitle {{
            background-color: {colors.get('basit_yellow', colors['warning'])};
            color: {colors.get('basit_category_text', colors['text_primary'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
            padding: 8px 10px;
            font-size: {value_px}px;
            font-weight: 950;
        }}
        QLabel#restaurantSimpleSectionSubtitle {{
            color: {colors['text_secondary']};
            font-size: {caption_px}px;
            padding: 0 4px 4px 4px;
        }}
        QPushButton#restaurantSimpleCategoryButton,
        QPushButton#restaurantSimpleItemButton,
        QPushButton[basitCard="true"] {{
            min-height: {BRAND.get('basit_category_card_height', 58)}px;
            background-color: {colors.get('basit_card_bg', colors['primary'])};
            color: {colors.get('basit_card_text', '#FFFFFF')};
            border: 1px solid {colors.get('basit_card_border', colors['primary'])};
            border-radius: 3px;
            padding: 8px 10px;
            font-size: {value_px}px;
            font-weight: 900;
            text-align: center;
        }}
        QPushButton#restaurantSimpleCategoryButton:hover,
        QPushButton#restaurantSimpleItemButton:hover,
        QPushButton[basitCard="true"]:hover {{
            background-color: {colors.get('basit_blue_hover', colors['primary_hover'])};
        }}
        QPushButton#restaurantSimpleCategoryButton:checked {{
            background-color: {colors.get('basit_category_bg', colors['warning'])};
            color: {colors.get('basit_category_text', colors['text_primary'])};
            border: 2px solid {colors.get('basit_red', colors['danger'])};
        }}
        QTableWidget#restaurantSimpleInvoiceTable,
        QTableView[basitTable="true"], QTableWidget[basitTable="true"] {{
            background-color: {colors.get('basit_table_bg', colors['bg_table'])};
            alternate-background-color: {colors.get('basit_table_alt', colors['bg_table_alt'])};
            gridline-color: {colors.get('basit_toolbar_border', colors['border'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
            selection-background-color: {colors.get('basit_yellow_soft', colors['selection_bg'])};
            selection-color: {colors['text_primary']};
            font-size: {table_pt}pt;
        }}
        QTableWidget#restaurantSimpleInvoiceTable::item,
        QTableView[basitTable="true"]::item, QTableWidget[basitTable="true"]::item {{
            min-height: {BRAND.get('basit_invoice_row_height', 36)}px;
            padding: 7px 8px;
        }}
        QTableWidget#restaurantSimpleInvoiceTable::item:selected,
        QTableView[basitTable="true"]::item:selected, QTableWidget[basitTable="true"]::item:selected {{
            background-color: {colors.get('basit_yellow_soft', colors['selection_bg'])};
            color: {colors['text_primary']};
            border: 1px solid {colors.get('basit_red', colors['danger'])};
        }}
        QTableWidget#restaurantSimpleInvoiceTable QHeaderView::section,
        QTableView[basitTable="true"] QHeaderView::section,
        QTableWidget[basitTable="true"] QHeaderView::section {{
            background-color: {colors.get('basit_table_header_bg', colors['table_header_bg'])};
            color: {colors.get('basit_table_header_text', colors['table_header_text'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            padding: 8px 10px;
            font-weight: 950;
        }}
        QFrame#restaurantSimpleFooter,
        QFrame[basitTotalFooter="true"] {{
            background-color: {colors.get('basit_toolbar_bg', colors['bg_panel'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
            min-height: {BRAND.get('basit_total_height', 58)}px;
        }}
        QLabel#restaurantSimpleTotal,
        QLabel[basitTotal="true"] {{
            background-color: {colors.get('basit_total_bg', colors['danger'])};
            color: {colors.get('basit_total_text', '#FFFFFF')};
            border: none;
            border-radius: 2px;
            padding: 10px 20px;
            font-size: 26px;
            font-weight: 950;
            qproperty-alignment: AlignCenter;
        }}
        QPushButton#restaurantSimpleCheckoutButton {{
            background-color: {colors.get('basit_red', colors['danger'])};
            color: {colors.get('basit_total_text', '#FFFFFF')};
            border: 1px solid {colors.get('basit_red_dark', colors['danger'])};
            border-radius: 3px;
            font-size: 16px;
            font-weight: 950;
        }}
        QPushButton#restaurantSimpleCheckoutButton:hover {{
            background-color: {colors.get('basit_red_dark', colors['danger'])};
        }}
        QPushButton#restaurantSimplePrintButton,
        QPushButton#restaurantSimpleRemoveLineButton,
        QPushButton#restaurantSimpleQtyPlusButton,
        QPushButton#restaurantSimpleQtyMinusButton {{
            background-color: {colors.get('basit_blue', colors['primary'])};
            color: #FFFFFF;
            border: 1px solid {colors.get('basit_card_border', colors['primary'])};
            border-radius: 3px;
            font-weight: 950;
        }}
        QPushButton[visualRole="dashboard_shortcut"] {{
            min-height: {BRAND.get('basit_dashboard_card_height', 96)}px;
            background-color: {colors.get('basit_blue', colors['primary'])};
            color: #FFFFFF;
            border: 1px solid {colors.get('basit_card_border', colors['primary'])};
            border-radius: 3px;
            font-weight: 950;
        }}
        QPushButton[visualRole="dashboard_shortcut"]:hover {{
            background-color: {colors.get('basit_blue_hover', colors['primary_hover'])};
        }}

        /* Phase403: Basit-inspired invoices and returns. */
        QFrame#TransactionInlineHeaderBar[basitToolbar="true"] {{
            background-color: {colors.get('basit_toolbar_bg', colors['bg_panel'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
            padding: 6px;
            min-height: {BRAND.get('basit_toolbar_height', 46)}px;
        }}
        QFrame#TransactionInlineHeaderBar[basitToolbar="true"] QLineEdit,
        QFrame#TransactionInlineHeaderBar[basitToolbar="true"] QComboBox,
        QFrame#TransactionInlineHeaderBar[basitToolbar="true"] QDateEdit,
        QFrame#TransactionInlineHeaderBar[basitToolbar="true"] QLabel {{
            min-height: 28px;
            font-weight: 800;
        }}
        QFrame#TransactionInlineHeaderBar[basitToolbar="true"] QLabel#TransactionInlineHeaderLabel {{
            color: {colors.get('basit_table_header_text', colors['text_primary'])};
            background-color: {colors.get('basit_yellow', colors['warning'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
            padding: 3px 6px;
        }}
        QPushButton[basitToolbarButton="true"],
        QToolButton[basitToolbarButton="true"] {{
            min-height: {BRAND.get('basit_toolbar_height', 46)}px;
            background-color: {colors.get('basit_blue', colors['primary'])};
            color: #FFFFFF;
            border: 1px solid {colors.get('basit_card_border', colors['primary'])};
            border-radius: 3px;
            padding: 6px 10px;
            font-weight: 950;
        }}
        QPushButton[basitToolbarButton="true"]:hover,
        QToolButton[basitToolbarButton="true"]:hover {{
            background-color: {colors.get('basit_blue_hover', colors['primary_hover'])};
        }}
        QTableView[basitTransactionGrid="true"] {{
            min-height: 430px;
        }}
        QFrame#TransactionHorizontalSummaryFrame[basitTransactionSummary="true"],
        QFrame#TransactionHorizontalPaymentFrame[basitTransactionPayment="true"] {{
            background-color: {colors.get('basit_table_bg', colors['bg_panel'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
            min-height: {BRAND.get('basit_total_height', 58)}px;
        }}
        QLabel#TransactionSummaryValue[basitTotal="true"] {{
            background-color: {colors.get('basit_total_bg', colors['danger'])};
            color: {colors.get('basit_total_text', '#FFFFFF')};
            border-radius: 2px;
            padding: 8px 16px;
            font-size: 22px;
            font-weight: 950;
        }}

        /* Phase404: Basit-inspired management/list workspaces. */
        QWidget[basitManagementWorkspace="true"] {{
            background-color: {colors.get('basit_canvas', colors['bg_window'])};
        }}
        QWidget[basitListToolbar="true"],
        QWidget[basitManagementWorkspace="true"] > QWidget[basitListToolbar="true"] {{
            background-color: {colors.get('basit_toolbar_bg', colors['bg_panel'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
            padding: 6px;
            min-height: {BRAND.get('basit_toolbar_height', 46)}px;
        }}
        QWidget[basitListToolbar="true"] QLineEdit[basitListSearch="true"],
        QWidget[basitManagementWorkspace="true"] QLineEdit[basitListSearch="true"],
        QWidget[basitManagementWorkspace="true"] QComboBox {{
            min-height: {BRAND.get('basit_toolbar_height', 46)}px;
            background-color: #FFFFFF;
            color: {colors['text_primary']};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 3px;
            padding: 6px 10px;
            font-weight: 850;
        }}
        QWidget[basitManagementWorkspace="true"] QLabel {{
            font-weight: 800;
        }}
        QWidget[basitListToolbar="true"] QLabel[basitCounter="true"],
        QWidget[basitManagementWorkspace="true"] QLabel#muted,
        QWidget[basitManagementWorkspace="true"] QLabel#mutedLabel {{
            background-color: {colors.get('basit_yellow', colors['warning'])};
            color: {colors.get('basit_category_text', colors['text_primary'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
            padding: 6px 10px;
            font-weight: 950;
        }}
        QWidget[basitManagementWorkspace="true"] QPushButton[basitToolbarButton="true"],
        QWidget[basitListToolbar="true"] QPushButton[basitToolbarButton="true"] {{
            min-height: {BRAND.get('basit_toolbar_height', 46)}px;
            background-color: {colors.get('basit_blue', colors['primary'])};
            color: #FFFFFF;
            border: 1px solid {colors.get('basit_card_border', colors['primary'])};
            border-radius: 3px;
            padding: 6px 11px;
            font-weight: 950;
        }}
        QWidget[basitManagementWorkspace="true"] QPushButton[basitToolbarButton="true"]:hover,
        QWidget[basitListToolbar="true"] QPushButton[basitToolbarButton="true"]:hover {{
            background-color: {colors.get('basit_blue_hover', colors['primary_hover'])};
        }}
        QWidget[basitManagementWorkspace="true"] QPushButton#danger[basitToolbarButton="true"],
        QWidget[basitListToolbar="true"] QPushButton#danger[basitToolbarButton="true"] {{
            background-color: {colors.get('basit_red', colors['danger'])};
            border-color: {colors.get('basit_red_dark', colors['danger'])};
            color: {colors.get('basit_total_text', '#FFFFFF')};
        }}
        QSplitter#ResponsiveMasterDetailSplitter[basitMasterDetailSplitter="true"] {{
            background-color: {colors.get('basit_canvas', colors['bg_window'])};
        }}
        QSplitter#ResponsiveMasterDetailSplitter[basitMasterDetailSplitter="true"]::handle {{
            background-color: {colors.get('basit_toolbar_border', colors['border'])};
            width: 4px;
            height: 4px;
        }}
        QFrame#DetailPlaceholder[basitDetailPlaceholder="true"] {{
            background-color: {colors.get('basit_table_bg', colors['bg_panel'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
            padding: 12px;
        }}
        QFrame#DetailPlaceholder[basitDetailPlaceholder="true"] QLabel#DetailTitle {{
            background-color: {colors.get('basit_yellow', colors['warning'])};
            color: {colors.get('basit_category_text', colors['text_primary'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
            padding: 8px 10px;
            font-size: {value_px}px;
            font-weight: 950;
        }}
        QFrame#DetailPlaceholder[basitDetailPlaceholder="true"] QLabel#DetailSubtitle,
        QFrame#DetailPlaceholder[basitDetailPlaceholder="true"] QLabel#DetailBody {{
            color: {colors['text_primary']};
            font-weight: 800;
        }}
        QWidget#UnifiedInlineEditorPage[basitInlineEditorPage="true"],
        QWidget#UnifiedInlineEditorHost[basitInlineEditorHost="true"] {{
            background-color: {colors.get('basit_canvas', colors['bg_window'])};
        }}
        QTableView[basitManagementTable="true"],
        QTableWidget[basitManagementTable="true"] {{
            min-height: 420px;
        }}

        QFrame[basitPanel="true"] {{
            background-color: {colors.get('basit_table_bg', colors['bg_panel'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
        }}


        /* Phase405: Basit-inspired reports and settings surfaces. */
        QWidget[basitReportsSurface="true"],
        QWidget#settingsWidget[basitSettingsSurface="true"] {{
            background-color: {colors.get('basit_canvas', colors['bg_window'])};
        }}
        QFrame#ReportsFilterToolbar[basitReportToolbar="true"] {{
            background-color: {colors.get('basit_toolbar_bg', colors['bg_panel'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
            min-height: {BRAND.get('basit_toolbar_height', 46)}px;
        }}
        QFrame#ReportsFilterToolbar[basitReportToolbar="true"] QLabel {{
            background-color: {colors.get('basit_yellow', colors['warning'])};
            color: {colors.get('basit_category_text', colors['text_primary'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
            padding: 5px 8px;
            font-weight: 950;
        }}
        QFrame#ReportsFilterToolbar[basitReportToolbar="true"] QComboBox,
        QFrame#ReportsFilterToolbar[basitReportToolbar="true"] QDateEdit,
        QWidget#settingsWidget[basitSettingsSurface="true"] QLineEdit,
        QWidget#settingsWidget[basitSettingsSurface="true"] QComboBox,
        QWidget#settingsWidget[basitSettingsSurface="true"] QSpinBox {{
            min-height: {BRAND.get('basit_toolbar_height', 46)}px;
            background-color: #FFFFFF;
            color: {colors['text_primary']};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 3px;
            padding: 6px 10px;
            font-weight: 850;
        }}
        QTabWidget[basitReportTabs="true"]::pane,
        QTabWidget#settingsTabs[basitSettingsTabs="true"]::pane,
        QTabWidget[basitSettingsGroupTabs="true"]::pane {{
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
            background: {colors.get('basit_table_bg', colors['bg_window'])};
        }}
        QTabWidget[basitReportTabs="true"] QTabBar::tab,
        QTabWidget#settingsTabs[basitSettingsTabs="true"] QTabBar::tab,
        QTabWidget[basitSettingsGroupTabs="true"] QTabBar::tab {{
            min-height: 34px;
            background: {colors.get('basit_blue', colors['primary'])};
            color: #FFFFFF;
            border: 1px solid {colors.get('basit_card_border', colors['primary'])};
            border-radius: 2px;
            padding: 7px 13px;
            margin: 1px;
            font-weight: 900;
        }}
        QTabWidget[basitReportTabs="true"] QTabBar::tab:selected,
        QTabWidget#settingsTabs[basitSettingsTabs="true"] QTabBar::tab:selected,
        QTabWidget[basitSettingsGroupTabs="true"] QTabBar::tab:selected {{
            background: {colors.get('basit_yellow', colors['warning'])};
            color: {colors.get('basit_category_text', colors['text_primary'])};
            border: 2px solid {colors.get('basit_red', colors['danger'])};
        }}
        QLabel#reportSummaryBar[basitReportSummary="true"] {{
            background-color: {colors.get('basit_total_bg', colors['danger'])};
            color: {colors.get('basit_total_text', '#FFFFFF')};
            border: 1px solid {colors.get('basit_red_dark', colors['danger'])};
            border-radius: 2px;
            padding: 8px 16px;
            min-height: {BRAND.get('basit_total_height', 58)}px;
            font-size: 18px;
            font-weight: 950;
        }}
        QGroupBox#settingsCard[basitSettingsCard="true"] {{
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
            background: {colors.get('basit_table_bg', colors['card_bg'])};
            color: {colors['text_primary']};
            font-weight: 900;
        }}
        QGroupBox#settingsCard[basitSettingsCard="true"]::title {{
            color: {colors.get('basit_category_text', colors['text_primary'])};
            background: {colors.get('basit_yellow', colors['warning'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
            border-radius: 2px;
            padding: 4px 10px;
        }}


        /* Phase434: branded pre-login startup splash; no legacy yellow header, no fake buttons. */
        QFrame#brandedStartupCard[startupSurfacePolicy="phase434_prelogin_branded"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #07365c,
                stop:0.55 #0b5371,
                stop:1 #0f8a82);
            border: 1px solid rgba(255,255,255,0.20);
            border-radius: 18px;
        }}
        QFrame#startupIdentityPanel[startupIdentityPanel="true"] {{
            background-color: rgba(255,255,255,0.055);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 16px;
            min-height: 168px;
        }}
        QLabel#startupBrandMark {{
            background: transparent;
            border: none;
        }}
        QLabel#startupHeroTitle {{
            background: transparent;
            color: #FFFFFF;
            font-size: 25px;
            font-weight: 900;
            letter-spacing: 0.2px;
        }}
        QLabel#startupHeroSubtitle {{
            background: transparent;
            color: rgba(255,255,255,0.82);
            font-size: 13px;
            font-weight: 700;
        }}
        QLabel[startupStageChip="true"] {{
            background-color: rgba(255,255,255,0.14);
            color: rgba(255,255,255,0.82);
            border: 1px solid rgba(255,255,255,0.16);
            border-radius: 14px;
            padding: 5px 12px;
            font-size: 11px;
            font-weight: 800;
            min-width: 92px;
        }}
        QLabel[startupStageChip="true"][state="active"] {{
            background-color: rgba(255,255,255,0.96);
            color: #083A63;
            border: 1px solid rgba(255,255,255,1.0);
        }}
        QLabel#startupStepLabel {{
            background: transparent;
            color: #FFFFFF;
            font-size: 13px;
            font-weight: 900;
        }}
        QProgressBar#startupProgressTrack {{
            background-color: rgba(255,255,255,0.22);
            border: none;
            border-radius: 7px;
            min-height: 14px;
            max-height: 14px;
            color: #FFFFFF;
            font-size: 10px;
            font-weight: 900;
            text-align: center;
        }}
        QProgressBar#startupProgressTrack::chunk {{
            background-color: #FFFFFF;
            border-radius: 7px;
        }}
        QProgressBar#startupProgressTrack[startupError="true"]::chunk {{
            background-color: #EF4444;
        }}
        QLabel#startupStatusLabel {{
            background: transparent;
            color: rgba(255,255,255,0.84);
            font-size: 12px;
            font-weight: 700;
        }}
        QLabel#startupDetailLabel {{
            background: transparent;
            color: rgba(255,255,255,0.66);
            font-size: 11px;
        }}
        QLabel#startupFooterLabel {{
            background: transparent;
            color: rgba(255,255,255,0.62);
            font-size: 10px;
            font-weight: 700;
        }}


        /* Phase435: login-to-main-window transition overlay. */
        QWidget#postLoginTransitionOverlay {{
            background: transparent;
        }}
        QFrame#postLoginTransitionCard {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {colors.get('brand_navy', colors['primary'])},
                stop:0.55 {colors.get('brand_blue', colors['primary_2'])},
                stop:1 {colors.get('brand_teal', colors['accent'])});
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 18px;
        }}
        QLabel#postLoginTransitionTitle {{
            background: transparent;
            color: #FFFFFF;
            font-size: 21px;
            font-weight: 900;
        }}
        QLabel#postLoginTransitionDetail,
        QLabel#postLoginTransitionHint {{
            background: transparent;
            color: rgba(255,255,255,0.74);
            font-size: 12px;
            font-weight: 700;
        }}
        QLabel#postLoginTransitionStatus {{
            background: rgba(255,255,255,0.12);
            color: #FFFFFF;
            border: 1px solid rgba(255,255,255,0.16);
            border-radius: 10px;
            padding: 8px 12px;
            font-size: 13px;
            font-weight: 900;
        }}
        QProgressBar#postLoginTransitionProgress {{
            background-color: rgba(255,255,255,0.20);
            border: none;
            border-radius: 6px;
        }}
        QProgressBar#postLoginTransitionProgress::chunk {{
            background-color: #FFFFFF;
            border-radius: 6px;
        }}


        /* Phase406: Basit-inspired shell chrome fallback. */
        QFrame#CleanShellNavigationBar[basitShellChrome="true"],
        QFrame#UnifiedActionBar[basitShellChrome="true"] {{
            background-color: {colors.get('basit_shell_bg', colors.get('basit_toolbar_bg', colors['bg_panel']))};
            border-bottom: 2px solid {colors.get('basit_toolbar_border', colors['border'])};
        }}
        QTabWidget#TabbedWorkspace[basitShellTabs="true"]::pane {{
            background-color: {colors.get('basit_canvas', colors['bg_window'])};
            border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
        }}

        /* Phase447: unified list workspace visual template.
           This block is intentionally placed after the older Basit list rules so
           every lazy-loaded list surface can override legacy toolbar/table skin
           without changing business logic. */
        QWidget[listWorkspaceVisualTemplatePhase="447"],
        QWidget[visualRole="list_workspace_surface"] {{
            background-color: {BRAND.get('list_workspace_surface_bg', colors.get('workspace_content_bg', colors['bg_window']))};
            color: {colors['text_primary']};
        }}
        QWidget[visualRole="list_filter_bar"],
        QWidget[listWorkspaceVisualTemplatePhase="447"][visualRole="list_filter_bar"],
        QWidget[basitListToolbar="true"][listWorkspaceVisualTemplatePhase="447"] {{
            background-color: {BRAND.get('list_workspace_filter_bg', colors.get('workspace_card_bg', colors['bg_panel']))};
            border: 1px solid {BRAND.get('list_workspace_filter_border', colors.get('workspace_card_border', colors['border']))};
            border-radius: {BRAND.get('list_workspace_filter_radius', radius_lg)}px;
            padding: 8px;
            min-height: 46px;
        }}
        QWidget[listWorkspaceVisualTemplatePhase="447"] QLineEdit,
        QWidget[listWorkspaceVisualTemplatePhase="447"] QComboBox,
        QWidget[listWorkspaceVisualTemplatePhase="447"] QDateEdit,
        QLineEdit[visualRole="list_search_input"],
        QLineEdit[visualRole="list_filter_input"],
        QComboBox[visualRole="list_filter_input"],
        QDateEdit[visualRole="list_filter_input"] {{
            min-height: 36px;
            background-color: {BRAND.get('list_workspace_input_bg', colors.get('input_bg', colors['bg_panel']))};
            color: {colors['text_primary']};
            border: 1px solid {BRAND.get('list_workspace_input_border', colors.get('workspace_card_border', colors['border']))};
            border-radius: {radius_md}px;
            padding: 5px 10px;
            font-weight: 750;
        }}
        QWidget[listWorkspaceVisualTemplatePhase="447"] QPushButton,
        QPushButton[visualRole="list_action"],
        QPushButton[visualRole="list_filter_action"] {{
            min-height: 38px;
            background-color: {BRAND.get('list_workspace_action_bg', colors.get('shell_action_utility_bg_phase446', colors['bg_panel']))};
            color: {BRAND.get('list_workspace_action_text', colors['text_primary'])};
            border: 1px solid {BRAND.get('list_workspace_filter_border', colors.get('workspace_card_border', colors['border']))};
            border-radius: {radius_md}px;
            padding: 7px 12px;
            font-weight: 850;
        }}
        QWidget[listWorkspaceVisualTemplatePhase="447"] QPushButton:hover,
        QPushButton[visualRole="list_action"]:hover,
        QPushButton[visualRole="list_filter_action"]:hover {{
            background-color: {colors.get('brand_soft', '#EAF4FF')};
            border-color: {colors.get('shell_navigation_active_indicator', colors['primary'])};
        }}
        QPushButton[visualRole="list_primary_action"],
        QWidget[listWorkspaceVisualTemplatePhase="447"] QPushButton#primary {{
            min-height: 40px;
            background-color: {BRAND.get('list_workspace_primary_bg', colors['primary'])};
            color: #FFFFFF;
            border: 1px solid {BRAND.get('list_workspace_primary_bg', colors['primary'])};
            border-radius: {radius_md}px;
            padding: 7px 14px;
            font-weight: 900;
        }}
        QPushButton[visualRole="list_primary_action"]:hover,
        QWidget[listWorkspaceVisualTemplatePhase="447"] QPushButton#primary:hover {{
            background-color: {BRAND.get('list_workspace_primary_hover', colors.get('primary_hover', colors['primary']))};
        }}
        QPushButton[visualRole="list_danger_action"],
        QWidget[listWorkspaceVisualTemplatePhase="447"] QPushButton#danger {{
            min-height: 38px;
            background-color: {BRAND.get('list_workspace_danger_bg', colors.get('danger_soft', '#FEE2E2'))};
            color: {BRAND.get('list_workspace_danger_text', colors['danger'])};
            border: 1px solid {colors.get('danger', BRAND.get('list_workspace_danger_text', '#B42318'))};
            border-radius: {radius_md}px;
            padding: 7px 12px;
            font-weight: 900;
        }}
        QLabel[visualRole="list_counter"],
        QWidget[listWorkspaceVisualTemplatePhase="447"] QLabel[basitCounter="true"] {{
            background-color: {BRAND.get('list_workspace_counter_bg', colors.get('workspace_section_header_bg', colors['brand_soft']))};
            color: {BRAND.get('list_workspace_counter_text', colors.get('workspace_section_header_text', colors['primary']))};
            border: 1px solid {BRAND.get('list_workspace_filter_border', colors.get('workspace_card_border', colors['border']))};
            border-radius: {radius_md}px;
            padding: 7px 12px;
            font-weight: 900;
        }}
        QFrame[visualRole="list_card"],
        QGroupBox[visualRole="list_card"] {{
            background-color: {BRAND.get('list_workspace_detail_bg', colors.get('workspace_card_bg', colors['bg_panel']))};
            border: 1px solid {BRAND.get('list_workspace_detail_border', colors.get('workspace_card_border', colors['border']))};
            border-radius: {BRAND.get('workspace_card_radius', radius_lg)}px;
        }}
        QTableView[visualRole="list_table"],
        QTableWidget[visualRole="list_table"] {{
            background-color: {colors.get('bg_table', colors.get('workspace_card_bg', '#FFFFFF'))};
            alternate-background-color: {colors.get('bg_table_alt', '#F6FAFE')};
            border: 1px solid {BRAND.get('list_workspace_filter_border', colors.get('workspace_card_border', colors['border']))};
            border-radius: {radius_md}px;
            gridline-color: {colors.get('workspace_card_border', colors['border'])};
        }}
        QTableView[visualRole="list_table"] QHeaderView::section,
        QTableWidget[visualRole="list_table"] QHeaderView::section {{
            background-color: {BRAND.get('list_workspace_table_header_bg', BRAND.get('materials_table_header_bg', colors.get('header_bg', colors['primary'])))};
            color: {BRAND.get('list_workspace_table_header_text', BRAND.get('materials_table_header_text', '#FFFFFF'))};
            font-weight: 900;
            padding: 8px;
            border: none;
            border-left: 1px solid {BRAND.get('list_workspace_filter_border', colors.get('workspace_card_border', colors['border']))};
        }}



        /* Phase448: Operational POS/Restaurant surface migration.  These
           selectors intentionally come after the older Basit selectors so the
           shared operational identity wins without changing business logic. */
        QWidget[operationalSurfacePhase="448"] {{
            background-color: {BRAND.get('operational_surface_bg', colors.get('bg_window'))};
            color: {colors['text_primary']};
        }}
        QFrame[visualRole="operational_header"],
        QFrame[visualRole="operational_panel"],
        QFrame[visualRole="operational_footer"],
        QWidget[visualRole="operational_payment_shell"] {{
            background-color: {BRAND.get('operational_panel_bg', colors.get('bg_panel'))};
            border: 1px solid {BRAND.get('operational_panel_border', colors.get('border'))};
            border-radius: {BRAND.get('operational_card_radius', radius_lg)}px;
        }}
        QLabel[visualRole="operational_section_title"],
        QLabel#restaurantSimpleSectionTitle {{
            background-color: {BRAND.get('operational_panel_header_bg', colors.get('brand_soft'))};
            color: {BRAND.get('operational_panel_header_text', colors.get('primary'))};
            border: 1px solid {BRAND.get('operational_panel_border', colors.get('border'))};
            border-radius: {BRAND.get('operational_section_radius', radius_md)}px;
            padding: 8px 12px;
            font-size: {value_px}px;
            font-weight: 950;
        }}
        QLabel[visualRole="operational_muted"],
        QWidget[operationalSurfacePhase="448"] QLabel#muted,
        QWidget[operationalSurfacePhase="448"] QLabel#restaurantSimpleSubtitle,
        QWidget[operationalSurfacePhase="448"] QLabel#restaurantSessionMeta {{
            color: {colors.get('text_secondary')};
            background: transparent;
            font-weight: 800;
        }}
        QLineEdit[visualRole="operational_scan_input"] {{
            min-height: {BRAND.get('operational_scan_input_min_height', 58)}px;
            background-color: {colors.get('input_bg', '#FFFFFF')};
            border: 2px solid {BRAND.get('operational_panel_border', colors.get('border'))};
            border-radius: {BRAND.get('operational_section_radius', radius_md)}px;
            padding: 8px 14px;
            font-size: 24px;
            font-weight: 950;
            color: {colors['text_primary']};
        }}
        QLineEdit[visualRole="operational_input"],
        QComboBox[visualRole="operational_select"],
        QDoubleSpinBox[visualRole="operational_spin"],
        QSpinBox[visualRole="operational_spin"] {{
            min-height: 40px;
            background-color: {colors.get('input_bg', '#FFFFFF')};
            border: 1px solid {BRAND.get('operational_panel_border', colors.get('border'))};
            border-radius: {radius_md}px;
            padding: 6px 10px;
            font-weight: 850;
        }}
        QPushButton[visualRole="operational_primary"],
        QToolButton[visualRole="operational_primary"] {{
            min-height: {BRAND.get('operational_action_min_height', 42)}px;
            background-color: {BRAND.get('operational_primary_bg', colors.get('primary'))};
            color: #FFFFFF;
            border: 1px solid {BRAND.get('operational_primary_bg', colors.get('primary'))};
            border-radius: {radius_md}px;
            padding: 8px 14px;
            font-weight: 950;
        }}
        QPushButton[visualRole="operational_primary"]:hover,
        QToolButton[visualRole="operational_primary"]:hover {{
            background-color: {BRAND.get('operational_primary_hover', colors.get('primary_hover'))};
        }}
        QPushButton[visualRole="operational_secondary"],
        QToolButton[visualRole="operational_secondary"] {{
            min-height: {BRAND.get('operational_action_min_height', 42)}px;
            background-color: {BRAND.get('operational_secondary_bg', colors.get('brand_soft'))};
            color: {BRAND.get('operational_secondary_text', colors.get('primary'))};
            border: 1px solid {BRAND.get('operational_panel_border', colors.get('border'))};
            border-radius: {radius_md}px;
            padding: 8px 13px;
            font-weight: 900;
        }}
        QPushButton[visualRole="operational_danger"],
        QToolButton[visualRole="operational_danger"] {{
            min-height: {BRAND.get('operational_action_min_height', 42)}px;
            background-color: {BRAND.get('operational_danger_bg', colors.get('danger_soft'))};
            color: {BRAND.get('operational_danger_text', colors.get('danger'))};
            border: 1px solid {BRAND.get('operational_danger_text', colors.get('danger'))};
            border-radius: {radius_md}px;
            padding: 8px 13px;
            font-weight: 900;
        }}
        QFrame[visualRole="operational_actions"] QPushButton,
        QWidget[operationalSurfacePhase="448"] QPushButton[basitToolbarButton="true"] {{
            border-radius: {radius_md}px;
        }}
        QTableView[visualRole="operational_table"],
        QTableWidget[visualRole="operational_table"],
        QWidget[operationalSurfacePhase="448"] QTableView[basitTable="true"],
        QWidget[operationalSurfacePhase="448"] QTableWidget[basitTable="true"] {{
            background-color: {colors.get('bg_table', '#FFFFFF')};
            alternate-background-color: {colors.get('bg_table_alt', '#F8FAFC')};
            border: 1px solid {BRAND.get('operational_panel_border', colors.get('border'))};
            border-radius: {radius_md}px;
            gridline-color: {colors.get('border')};
            selection-background-color: {colors.get('selection_bg')};
            selection-color: {colors.get('selection_text')};
        }}
        QTableView[visualRole="operational_table"] QHeaderView::section,
        QTableWidget[visualRole="operational_table"] QHeaderView::section,
        QWidget[operationalSurfacePhase="448"] QTableView[basitTable="true"] QHeaderView::section,
        QWidget[operationalSurfacePhase="448"] QTableWidget[basitTable="true"] QHeaderView::section {{
            background-color: {BRAND.get('operational_panel_header_bg', colors.get('brand_soft'))};
            color: {BRAND.get('operational_panel_header_text', colors.get('primary'))};
            border: none;
            border-left: 1px solid {BRAND.get('operational_panel_border', colors.get('border'))};
            padding: 8px;
            font-weight: 950;
        }}
        QLabel[visualRole="operational_total"],
        QWidget[operationalSurfacePhase="448"] QLabel#restaurantSimpleTotal,
        QWidget[operationalSurfacePhase="448"] QLabel[basitTotal="true"] {{
            background-color: {BRAND.get('operational_total_bg', colors.get('danger'))};
            color: {BRAND.get('operational_total_text', '#FFFFFF')};
            border-radius: {BRAND.get('operational_section_radius', radius_md)}px;
            padding: 10px 18px;
            font-size: 24px;
            font-weight: 950;
            qproperty-alignment: AlignCenter;
        }}
        QWidget[operationalSurfacePhase="448"] QPushButton#operationalItemCardButton,
        QWidget[operationalSurfacePhase="448"] QPushButton#restaurantSimpleCategoryButton,
        QWidget[operationalSurfacePhase="448"] QPushButton[basitCard="true"] {{
            background-color: {colors.get('card_bg', '#FFFFFF')};
            color: {colors.get('text_primary')};
            border: 1px solid {BRAND.get('operational_panel_border', colors.get('border'))};
            border-radius: {BRAND.get('operational_section_radius', radius_md)}px;
            padding: 8px 10px;
            font-weight: 900;
        }}
        QWidget[operationalSurfacePhase="448"] QPushButton#restaurantSimpleCategoryButton:checked {{
            background-color: {BRAND.get('operational_primary_bg', colors.get('primary'))};
            color: #FFFFFF;
            border: 1px solid {BRAND.get('operational_primary_bg', colors.get('primary'))};
        }}
        QWidget[operationalSurfacePhase="448"] QFrame#restaurantActionGroups,
        QWidget[operationalSurfacePhase="448"] QFrame#restaurantOrderSummaryCard,
        QWidget[operationalSurfacePhase="448"] QFrame#restaurantMenuToggleCard {{
            background-color: {BRAND.get('operational_panel_bg', colors.get('bg_panel'))};
            border: 1px solid {BRAND.get('operational_panel_border', colors.get('border'))};
            border-radius: {BRAND.get('operational_card_radius', radius_lg)}px;
        }}



        /* Phase449: reports workspace visual refactor.  The reports screen uses
           a filter ribbon + grouped report tabs + accounting tables.  These
           selectors come after older Basit/list/operational rules so report
           chrome no longer looks like a stacked toolbar of legacy buttons. */
        QWidget[reportsVisualPhase="449"],
        QWidget[visualRole="reports_workspace"] {{
            background-color: {BRAND.get('list_workspace_surface_bg', colors.get('bg_window'))};
            color: {colors['text_primary']};
        }}
        QFrame[visualRole="reports_filter_ribbon"] {{
            background-color: {BRAND.get('reports_filter_ribbon_bg', '#FFFFFF')};
            border: 1px solid {BRAND.get('reports_filter_ribbon_border', colors.get('border'))};
            border-radius: {BRAND.get('list_workspace_filter_radius', radius_lg)}px;
            padding: 4px;
        }}
        QWidget[reportsVisualPhase="449"] QComboBox[visualRole="reports_filter_input"],
        QWidget[reportsVisualPhase="449"] QDateEdit[visualRole="reports_filter_input"] {{
            min-height: 34px;
            background-color: {BRAND.get('reports_filter_input_bg', '#F8FBFF')};
            border: 1px solid {BRAND.get('reports_filter_input_border', colors.get('border'))};
            border-radius: {radius_md}px;
            padding: 5px 9px;
            font-weight: 800;
        }}
        QWidget[reportsVisualPhase="449"] QPushButton[visualRole="reports_primary_action"] {{
            min-height: 36px;
            background-color: {BRAND.get('reports_primary_bg', colors.get('primary'))};
            color: #FFFFFF;
            border: 1px solid {BRAND.get('reports_primary_bg', colors.get('primary'))};
            border-radius: {radius_md}px;
            padding: 7px 13px;
            font-weight: 950;
        }}
        QWidget[reportsVisualPhase="449"] QPushButton[visualRole="reports_primary_action"]:hover {{
            background-color: {BRAND.get('reports_primary_hover', colors.get('primary_hover'))};
        }}
        QWidget[reportsVisualPhase="449"] QPushButton[visualRole="reports_secondary_action"] {{
            min-height: 36px;
            background-color: {BRAND.get('list_workspace_action_bg', '#F8FBFC')};
            color: {BRAND.get('list_workspace_action_text', colors.get('text_primary'))};
            border: 1px solid {BRAND.get('reports_filter_input_border', colors.get('border'))};
            border-radius: {radius_md}px;
            padding: 7px 13px;
            font-weight: 900;
        }}
        QTabWidget[visualRole="reports_group_tabs"]::pane,
        QTabWidget[visualRole="reports_inner_tabs"]::pane {{
            border: 1px solid {BRAND.get('reports_filter_ribbon_border', colors.get('border'))};
            border-radius: {radius_md}px;
            background-color: {colors.get('bg_table', '#FFFFFF')};
            top: -1px;
        }}
        QTabWidget[visualRole="reports_group_tabs"] QTabBar::tab {{
            min-height: 36px;
            background-color: {BRAND.get('reports_group_tab_bg', colors.get('brand_soft'))};
            color: {BRAND.get('list_workspace_counter_text', colors.get('primary'))};
            border: 1px solid {BRAND.get('reports_filter_ribbon_border', colors.get('border'))};
            border-bottom: none;
            border-top-left-radius: {radius_md}px;
            border-top-right-radius: {radius_md}px;
            padding: 8px 14px;
            font-weight: 950;
        }}
        QTabWidget[visualRole="reports_group_tabs"] QTabBar::tab:selected {{
            background-color: {BRAND.get('reports_group_tab_active_bg', colors.get('primary'))};
            color: #FFFFFF;
        }}
        QTabWidget[visualRole="reports_inner_tabs"] QTabBar::tab {{
            min-height: 32px;
            background-color: {BRAND.get('reports_inner_tab_bg', '#F8FBFC')};
            color: {colors.get('text_secondary')};
            border: 1px solid {BRAND.get('reports_filter_ribbon_border', colors.get('border'))};
            border-bottom: none;
            padding: 6px 11px;
            font-weight: 850;
        }}
        QTabWidget[visualRole="reports_inner_tabs"] QTabBar::tab:selected {{
            background-color: {BRAND.get('reports_inner_tab_active_bg', colors.get('brand_soft'))};
            color: {BRAND.get('reports_table_header_text', colors.get('primary'))};
        }}
        QTableView[visualRole="reports_table"],
        QTableWidget[visualRole="reports_table"] {{
            background-color: {colors.get('bg_table', '#FFFFFF')};
            alternate-background-color: {colors.get('bg_table_alt', '#F8FAFC')};
            border: 1px solid {BRAND.get('reports_filter_ribbon_border', colors.get('border'))};
            border-radius: {radius_md}px;
            gridline-color: {colors.get('border')};
            selection-background-color: {colors.get('selection_bg')};
            selection-color: {colors.get('selection_text')};
        }}
        QTableView[visualRole="reports_table"] QHeaderView::section,
        QTableWidget[visualRole="reports_table"] QHeaderView::section {{
            background-color: {BRAND.get('reports_table_header_bg', colors.get('brand_soft'))};
            color: {BRAND.get('reports_table_header_text', colors.get('primary'))};
            border: none;
            border-left: 1px solid {BRAND.get('reports_filter_ribbon_border', colors.get('border'))};
            padding: 8px;
            font-weight: 950;
        }}
        QLabel[visualRole="reports_summary_bar"] {{
            background-color: {BRAND.get('reports_summary_bg', colors.get('warning_soft'))};
            color: {BRAND.get('reports_summary_text', colors.get('warning'))};
            border: 1px solid {BRAND.get('reports_filter_ribbon_border', colors.get('border'))};
            border-radius: {radius_md}px;
            padding: 8px 12px;
            font-weight: 950;
        }}


        /* Phase450: unified document editor visual template.  This covers
           invoice/return editors, voucher/expense editors, warehouse transfer,
           manufacturing documents, parties, categories and other BaseDocumentTab
           surfaces through document_layout_policy metadata. */
        QWidget[documentVisualTemplatePhase="450"],
        QWidget[visualRole="document_editor_surface"] {{
            background-color: {BRAND.get('document_editor_surface_bg', colors.get('workspace_content_bg', colors['bg_window']))};
            color: {colors['text_primary']};
        }}
        QFrame[visualRole="document_header"],
        QWidget[visualRole="document_header"] {{
            background-color: {BRAND.get('document_editor_header_bg', colors.get('workspace_card_bg', colors['bg_panel']))};
            border: 1px solid {BRAND.get('document_editor_header_border', colors.get('workspace_card_border', colors['border']))};
            border-radius: {BRAND.get('workspace_card_radius', radius_lg)}px;
            padding: 6px;
        }}
        QFrame[visualRole="document_card"],
        QGroupBox[visualRole="document_card"],
        QWidget[visualRole="document_card"] {{
            background-color: {BRAND.get('document_editor_card_bg', colors.get('workspace_card_bg', colors['bg_panel']))};
            border: 1px solid {BRAND.get('document_editor_card_border', colors.get('workspace_card_border', colors['border']))};
            border-radius: {BRAND.get('workspace_card_radius', radius_lg)}px;
        }}
        QFrame[visualRole="document_summary"],
        QWidget[visualRole="document_summary"] {{
            background-color: {BRAND.get('document_editor_summary_bg', colors.get('warning_soft', colors.get('workspace_card_bg', colors['bg_panel'])))};
            border: 1px solid {BRAND.get('document_editor_summary_border', colors.get('workspace_card_border', colors['border']))};
            border-radius: {BRAND.get('workspace_card_radius', radius_lg)}px;
        }}
        QFrame[visualRole="document_action_bar"],
        QWidget[visualRole="document_action_bar"] {{
            background-color: {BRAND.get('document_editor_action_bar_bg', colors.get('shell_action_bar_bg', colors['bg_panel']))};
            border: 1px solid {BRAND.get('document_editor_card_border', colors.get('workspace_card_border', colors['border']))};
            border-radius: {BRAND.get('workspace_card_radius', radius_lg)}px;
        }}
        QWidget[visualRole="document_header_field"] {{
            background-color: {colors.get('workspace_card_bg', '#FFFFFF')};
            border: 1px solid {BRAND.get('document_editor_input_border', colors.get('border'))};
            border-radius: {radius_md}px;
        }}
        QLabel[visualRole="document_title"] {{
            background: transparent;
            color: {colors.get('workspace_section_header_text', colors.get('primary'))};
            font-size: {title_px}px;
            font-weight: 950;
        }}
        QLabel[visualRole="document_subtitle"] {{
            background: transparent;
            color: {colors.get('text_secondary')};
            font-weight: 800;
        }}
        QLabel[visualRole="document_section_title"] {{
            background-color: {colors.get('workspace_section_header_bg', colors.get('brand_soft'))};
            color: {colors.get('workspace_section_header_text', colors.get('primary'))};
            border: 1px solid {BRAND.get('document_editor_card_border', colors.get('workspace_card_border', colors['border']))};
            border-radius: {radius_md}px;
            padding: 7px 11px;
            font-weight: 950;
        }}
        QLabel[visualRole="document_metric_title"] {{
            background: transparent;
            color: {BRAND.get('document_editor_metric_title', colors.get('text_secondary'))};
            font-size: {caption_px}px;
            font-weight: 850;
        }}
        QLabel[visualRole="document_metric_value"] {{
            background: transparent;
            color: {BRAND.get('document_editor_metric_value', colors.get('primary'))};
            font-size: {value_px}px;
            font-weight: 950;
        }}
        QWidget[documentVisualTemplatePhase="450"] QLineEdit,
        QWidget[documentVisualTemplatePhase="450"] QComboBox,
        QWidget[documentVisualTemplatePhase="450"] QDateEdit,
        QWidget[documentVisualTemplatePhase="450"] QTextEdit,
        QWidget[documentVisualTemplatePhase="450"] QSpinBox,
        QWidget[documentVisualTemplatePhase="450"] QDoubleSpinBox,
        QLineEdit[visualRole="document_input"],
        QComboBox[visualRole="document_input"],
        QDateEdit[visualRole="document_input"],
        QTextEdit[visualRole="document_input"],
        QSpinBox[visualRole="document_input"],
        QDoubleSpinBox[visualRole="document_input"] {{
            min-height: 36px;
            background-color: {BRAND.get('document_editor_input_bg', colors.get('input_bg', '#FFFFFF'))};
            color: {colors['text_primary']};
            border: 1px solid {BRAND.get('document_editor_input_border', colors.get('border'))};
            border-radius: {radius_md}px;
            padding: 5px 9px;
            font-weight: 800;
        }}
        QWidget[documentVisualTemplatePhase="450"] QLineEdit:focus,
        QWidget[documentVisualTemplatePhase="450"] QComboBox:focus,
        QWidget[documentVisualTemplatePhase="450"] QDateEdit:focus,
        QWidget[documentVisualTemplatePhase="450"] QTextEdit:focus,
        QWidget[documentVisualTemplatePhase="450"] QSpinBox:focus,
        QWidget[documentVisualTemplatePhase="450"] QDoubleSpinBox:focus {{
            border: 1px solid {colors.get('border_focus', colors.get('primary'))};
        }}
        QTableView[visualRole="document_table"],
        QTableWidget[visualRole="document_table"],
        QWidget[documentVisualTemplatePhase="450"] QTableView,
        QWidget[documentVisualTemplatePhase="450"] QTableWidget {{
            background-color: {colors.get('bg_table', '#FFFFFF')};
            alternate-background-color: {colors.get('bg_table_alt', '#F8FAFC')};
            border: 1px solid {BRAND.get('document_editor_card_border', colors.get('border'))};
            border-radius: {radius_md}px;
            gridline-color: {colors.get('border')};
            selection-background-color: {colors.get('selection_bg')};
            selection-color: {colors.get('selection_text')};
        }}
        QTableView[visualRole="document_table"] QHeaderView::section,
        QTableWidget[visualRole="document_table"] QHeaderView::section,
        QWidget[documentVisualTemplatePhase="450"] QTableView QHeaderView::section,
        QWidget[documentVisualTemplatePhase="450"] QTableWidget QHeaderView::section {{
            background-color: {BRAND.get('document_editor_table_header_bg', colors.get('brand_soft'))};
            color: {BRAND.get('document_editor_table_header_text', colors.get('primary'))};
            border: none;
            border-left: 1px solid {BRAND.get('document_editor_card_border', colors.get('border'))};
            padding: 8px;
            font-weight: 950;
        }}
        QPushButton[visualRole="document_primary_action"],
        QWidget[documentVisualTemplatePhase="450"] QPushButton#primary {{
            min-height: 40px;
            background-color: {BRAND.get('document_editor_primary_bg', colors.get('primary'))};
            color: #FFFFFF;
            border: 1px solid {BRAND.get('document_editor_primary_bg', colors.get('primary'))};
            border-radius: {radius_md}px;
            padding: 7px 15px;
            font-weight: 950;
        }}
        QPushButton[visualRole="document_primary_action"]:hover,
        QWidget[documentVisualTemplatePhase="450"] QPushButton#primary:hover {{
            background-color: {BRAND.get('document_editor_primary_hover', colors.get('primary_hover'))};
        }}
        QPushButton[visualRole="document_action"],
        QWidget[documentVisualTemplatePhase="450"] QPushButton {{
            min-height: 38px;
            background-color: {BRAND.get('document_editor_secondary_bg', '#FFFFFF')};
            color: {BRAND.get('document_editor_secondary_text', colors.get('text_primary'))};
            border: 1px solid {BRAND.get('document_editor_card_border', colors.get('border'))};
            border-radius: {radius_md}px;
            padding: 7px 13px;
            font-weight: 900;
        }}
        QPushButton[visualRole="document_action"]:hover,
        QWidget[documentVisualTemplatePhase="450"] QPushButton:hover {{
            background-color: {colors.get('brand_soft', '#EAF4FF')};
            border-color: {colors.get('shell_navigation_active_indicator', colors.get('primary'))};
        }}
        QPushButton[visualRole="document_danger_action"] {{
            min-height: 38px;
            background-color: {BRAND.get('document_editor_danger_bg', colors.get('danger_soft'))};
            color: {BRAND.get('document_editor_danger_text', colors.get('danger'))};
            border: 1px solid {BRAND.get('document_editor_danger_text', colors.get('danger'))};
            border-radius: {radius_md}px;
            padding: 7px 13px;
            font-weight: 900;
        }}
        QSplitter[visualRole="document_splitter"]::handle {{
            background-color: {BRAND.get('document_editor_card_border', colors.get('border'))};
            border-radius: 3px;
        }}

        /* Phase451: settings workspace visual consolidation.  Settings uses a
           two-level navigation model plus many form cards; these selectors
           deliberately come after Basit/Modern/page-local rules so the
           centralized settings identity wins without changing SettingsService
           persistence or individual save handlers. */
        QWidget[settingsVisualPhase="451"],
        QWidget[visualRole="settings_workspace"],
        QWidget[visualRole="settings_document_surface"] {{
            background-color: {BRAND.get('settings_workspace_surface_bg', colors.get('workspace_content_bg', colors['bg_window']))};
            color: {colors['text_primary']};
        }}
        QScrollArea[visualRole="settings_scroll"] {{
            border: none;
            background: transparent;
        }}
        QWidget[visualRole="settings_scroll_page"] {{
            background-color: {BRAND.get('settings_workspace_surface_bg', colors.get('workspace_content_bg', colors['bg_window']))};
        }}
        QTabWidget[visualRole="settings_group_tabs"]::pane,
        QTabWidget[visualRole="settings_leaf_tabs"]::pane {{
            border: 1px solid {BRAND.get('settings_workspace_panel_border', colors.get('workspace_card_border', colors['border']))};
            border-radius: {BRAND.get('workspace_card_radius', radius_lg)}px;
            background-color: {BRAND.get('settings_workspace_panel_bg', colors.get('workspace_card_bg', colors['bg_panel']))};
            top: -1px;
        }}
        QTabWidget[visualRole="settings_group_tabs"] QTabBar::tab {{
            min-height: 38px;
            background-color: {BRAND.get('settings_workspace_group_tab_bg', colors.get('brand_soft'))};
            color: {colors.get('workspace_section_header_text', colors.get('primary'))};
            border: 1px solid {BRAND.get('settings_workspace_panel_border', colors.get('border'))};
            border-radius: {radius_md}px;
            padding: 8px 16px;
            margin: 3px;
            font-weight: 900;
        }}
        QTabWidget[visualRole="settings_group_tabs"] QTabBar::tab:selected {{
            background-color: {BRAND.get('settings_workspace_group_tab_active_bg', colors.get('primary'))};
            color: {BRAND.get('settings_workspace_group_tab_active_text', '#FFFFFF')};
            border-color: {BRAND.get('settings_workspace_group_tab_active_bg', colors.get('primary'))};
        }}
        QTabWidget[visualRole="settings_leaf_tabs"] QTabBar::tab {{
            min-height: 34px;
            background-color: {BRAND.get('settings_workspace_leaf_tab_bg', colors.get('bg_panel'))};
            color: {colors.get('text_secondary')};
            border: 1px solid {BRAND.get('settings_workspace_panel_border', colors.get('border'))};
            border-radius: {radius_md}px;
            padding: 7px 13px;
            margin: 2px;
            font-weight: 850;
        }}
        QTabWidget[visualRole="settings_leaf_tabs"] QTabBar::tab:selected {{
            background-color: {BRAND.get('settings_workspace_leaf_tab_active_bg', colors.get('brand_soft'))};
            color: {colors.get('workspace_section_header_text', colors.get('primary'))};
            border-color: {colors.get('shell_navigation_active_indicator', colors.get('primary'))};
        }}
        QGroupBox[visualRole="settings_card"],
        QFrame[visualRole="settings_card"],
        QFrame[visualRole="settings_header"] {{
            background-color: {BRAND.get('settings_workspace_card_bg', colors.get('workspace_card_bg', colors['bg_panel']))};
            border: 1px solid {BRAND.get('settings_workspace_card_border', colors.get('workspace_card_border', colors['border']))};
            border-radius: {BRAND.get('workspace_card_radius', radius_lg)}px;
        }}
        QGroupBox[visualRole="settings_card"] {{
            margin-top: 14px;
            padding-top: 14px;
            font-weight: 950;
        }}
        QGroupBox[visualRole="settings_card"]::title {{
            subcontrol-origin: margin;
            right: 14px;
            padding: 4px 10px;
            color: {BRAND.get('settings_workspace_card_title_text', colors.get('primary'))};
            background-color: {BRAND.get('settings_workspace_card_title_bg', colors.get('brand_soft'))};
            border: 1px solid {BRAND.get('settings_workspace_card_border', colors.get('border'))};
            border-radius: {radius_md}px;
        }}
        QLabel[visualRole="settings_title"] {{
            background: transparent;
            color: {colors.get('workspace_section_header_text', colors.get('primary'))};
            font-size: {title_px}px;
            font-weight: 950;
        }}
        QLabel[visualRole="settings_help"] {{
            background: transparent;
            color: {colors.get('text_secondary')};
            font-weight: 800;
        }}
        QLineEdit[visualRole="settings_input"],
        QComboBox[visualRole="settings_input"],
        QSpinBox[visualRole="settings_input"],
        QDoubleSpinBox[visualRole="settings_input"],
        QDateEdit[visualRole="settings_input"],
        QTextEdit[visualRole="settings_input"],
        QPlainTextEdit[visualRole="settings_input"] {{
            min-height: 36px;
            background-color: {BRAND.get('settings_workspace_input_bg', colors.get('input_bg', '#FFFFFF'))};
            color: {colors['text_primary']};
            border: 1px solid {BRAND.get('settings_workspace_input_border', colors.get('border'))};
            border-radius: {radius_md}px;
            padding: 6px 10px;
            font-weight: 800;
        }}
        QCheckBox[visualRole="settings_input"] {{
            background: transparent;
            color: {colors['text_primary']};
            font-weight: 850;
            min-height: 30px;
        }}
        QPushButton[visualRole="settings_primary_action"] {{
            min-height: 40px;
            background-color: {BRAND.get('settings_workspace_primary_bg', colors.get('primary'))};
            color: #FFFFFF;
            border: 1px solid {BRAND.get('settings_workspace_primary_bg', colors.get('primary'))};
            border-radius: {radius_md}px;
            padding: 8px 16px;
            font-weight: 950;
        }}
        QPushButton[visualRole="settings_primary_action"]:hover {{
            background-color: {BRAND.get('settings_workspace_primary_hover', colors.get('primary_hover'))};
        }}
        QPushButton[visualRole="settings_action"] {{
            min-height: 38px;
            background-color: {BRAND.get('settings_workspace_secondary_bg', '#FFFFFF')};
            color: {BRAND.get('settings_workspace_secondary_text', colors.get('text_primary'))};
            border: 1px solid {BRAND.get('settings_workspace_card_border', colors.get('border'))};
            border-radius: {radius_md}px;
            padding: 7px 13px;
            font-weight: 900;
        }}
        QPushButton[visualRole="settings_action"]:hover {{
            background-color: {colors.get('brand_soft', '#EAF4FF')};
            border-color: {colors.get('shell_navigation_active_indicator', colors.get('primary'))};
        }}
        QPushButton[visualRole="settings_danger_action"] {{
            min-height: 38px;
            background-color: {BRAND.get('settings_workspace_note_danger_bg', colors.get('danger_soft'))};
            color: {BRAND.get('settings_workspace_note_danger_text', colors.get('danger'))};
            border: 1px solid {BRAND.get('settings_workspace_note_danger_border', colors.get('danger'))};
            border-radius: {radius_md}px;
            padding: 7px 13px;
            font-weight: 900;
        }}
        QLabel[visualRole="settings_note"] {{
            border-radius: {radius_md}px;
            padding: 10px 12px;
            font-weight: 850;
        }}
        QLabel[visualRole="settings_note"][settingsNoteTone="info"] {{
            background-color: {BRAND.get('settings_workspace_note_info_bg', colors.get('info_soft'))};
            border: 1px solid {BRAND.get('settings_workspace_note_info_border', colors.get('border'))};
            color: {BRAND.get('settings_workspace_note_info_text', colors.get('primary'))};
        }}
        QLabel[visualRole="settings_note"][settingsNoteTone="warning"] {{
            background-color: {BRAND.get('settings_workspace_note_warning_bg', colors.get('warning_soft'))};
            border: 1px solid {BRAND.get('settings_workspace_note_warning_border', colors.get('warning'))};
            color: {BRAND.get('settings_workspace_note_warning_text', colors.get('warning'))};
        }}
        QLabel[visualRole="settings_note"][settingsNoteTone="danger"],
        QLabel[visualRole="settings_note"][settingsNoteTone="error"] {{
            background-color: {BRAND.get('settings_workspace_note_danger_bg', colors.get('danger_soft'))};
            border: 1px solid {BRAND.get('settings_workspace_note_danger_border', colors.get('danger'))};
            color: {BRAND.get('settings_workspace_note_danger_text', colors.get('danger'))};
        }}
        QTableView[visualRole="settings_table"],
        QTableWidget[visualRole="settings_table"],
        EditableSmartGrid[visualRole="settings_table"] {{
            background-color: {colors.get('bg_table', '#FFFFFF')};
            alternate-background-color: {colors.get('bg_table_alt', '#F8FAFC')};
            border: 1px solid {BRAND.get('settings_workspace_card_border', colors.get('border'))};
            border-radius: {radius_md}px;
            gridline-color: {colors.get('border')};
            selection-background-color: {colors.get('selection_bg')};
            selection-color: {colors.get('selection_text')};
        }}
        QTableView[visualRole="settings_table"] QHeaderView::section,
        QTableWidget[visualRole="settings_table"] QHeaderView::section {{
            background-color: {BRAND.get('settings_workspace_table_header_bg', colors.get('brand_soft'))};
            color: {BRAND.get('settings_workspace_table_header_text', colors.get('primary'))};
            border: none;
            border-left: 1px solid {BRAND.get('settings_workspace_card_border', colors.get('border'))};
            padding: 8px;
            font-weight: 950;
        }}


        /* Phase452: dialogs and modal windows visual unification. */
        QDialog[modalVisualPhase="452"],
        QMessageBox[modalVisualPhase="452"] {{
            background-color: {BRAND.get('modal_surface_bg', colors.get('surface_root', colors['bg_window']))};
            color: {colors['text_primary']};
            border-radius: {BRAND.get('workspace_card_radius', radius_lg)}px;
        }}
        QDialog[modalVisualPhase="452"] QFrame#BrandDialogFrame,
        QDialog[modalVisualPhase="452"] QFrame[visualRole="modal_shell"],
        QMessageBox[modalVisualPhase="452"] {{
            background-color: {BRAND.get('modal_shell_bg', colors.get('bg_panel', '#FFFFFF'))};
            border: 1px solid {BRAND.get('modal_shell_border', colors.get('border'))};
            border-radius: {BRAND.get('workspace_card_radius', radius_lg)}px;
        }}
        QDialog[modalVisualPhase="452"] QFrame#BrandDialogHeader,
        QDialog[modalVisualPhase="452"] QFrame[visualRole="modal_header"] {{
            min-height: {BRAND.get('brand_dialog_header_height', dialog_header_height)}px;
            background-color: {BRAND.get('modal_header_bg', colors.get('brand_soft'))};
            color: {BRAND.get('modal_header_text', colors.get('primary'))};
            border-bottom: 3px solid {BRAND.get('modal_header_accent', colors.get('accent'))};
            border-top-left-radius: {BRAND.get('workspace_card_radius', radius_lg)}px;
            border-top-right-radius: {BRAND.get('workspace_card_radius', radius_lg)}px;
        }}
        QDialog[modalVisualPhase="452"] QWidget[visualRole="modal_body"],
        QDialog[modalVisualPhase="452"] QWidget[dialogSurface="body"] {{
            background-color: {BRAND.get('modal_body_bg', colors.get('bg_panel', '#FFFFFF'))};
            color: {colors['text_primary']};
        }}
        QDialog[modalVisualPhase="452"] QWidget[visualRole="modal_footer"],
        QDialog[modalVisualPhase="452"] QDialogButtonBox[visualRole="modal_button_box"],
        QDialog[modalVisualPhase="452"] QDialogButtonBox[dialogSurface="footer"] {{
            background-color: {BRAND.get('modal_footer_bg', colors.get('bg_window'))};
            border-top: 1px solid {BRAND.get('modal_shell_border', colors.get('border'))};
            padding: 10px;
        }}
        QDialog[modalVisualPhase="452"] QLabel#BrandDialogTitle,
        QDialog[modalVisualPhase="452"] QLabel[visualRole="modal_title"],
        QMessageBox[modalVisualPhase="452"] QLabel[visualRole="modal_title"] {{
            background: transparent;
            color: {BRAND.get('modal_header_text', colors.get('primary'))};
            font-size: {title_px}px;
            font-weight: 950;
        }}
        QDialog[modalVisualPhase="452"] QLabel[visualRole="modal_help"],
        QDialog[modalVisualPhase="452"] QLabel[visualRole="modal_status"],
        QMessageBox[modalVisualPhase="452"] QLabel {{
            background: transparent;
            color: {BRAND.get('modal_status_text', colors.get('text_secondary'))};
            font-weight: 820;
        }}
        QDialog[modalVisualPhase="452"] QLabel[modalTone="warning"],
        QMessageBox[modalVisualPhase="452"][modalTone="warning"] {{
            background-color: {BRAND.get('modal_warning_bg', colors.get('warning_soft'))};
            border: 1px solid {BRAND.get('modal_warning_border', colors.get('warning'))};
            border-radius: {radius_md}px;
            color: {BRAND.get('settings_workspace_note_warning_text', colors.get('warning'))};
            padding: 9px 11px;
        }}
        QDialog[modalVisualPhase="452"] QLabel[modalTone="danger"],
        QMessageBox[modalVisualPhase="452"][modalTone="danger"],
        QMessageBox[modalVisualPhase="452"][dialogKind="message_error"] {{
            background-color: {BRAND.get('modal_danger_bg', colors.get('danger_soft'))};
            border: 1px solid {BRAND.get('modal_danger_text', colors.get('danger'))};
            border-radius: {radius_md}px;
            color: {BRAND.get('modal_danger_text', colors.get('danger'))};
            padding: 9px 11px;
        }}
        QDialog[modalVisualPhase="452"] QLineEdit[visualRole="modal_input"],
        QDialog[modalVisualPhase="452"] QComboBox[visualRole="modal_input"],
        QDialog[modalVisualPhase="452"] QSpinBox[visualRole="modal_input"],
        QDialog[modalVisualPhase="452"] QDoubleSpinBox[visualRole="modal_input"],
        QDialog[modalVisualPhase="452"] QDateEdit[visualRole="modal_input"],
        QDialog[modalVisualPhase="452"] QTextEdit[visualRole="modal_input"],
        QDialog[modalVisualPhase="452"] QPlainTextEdit[visualRole="modal_input"] {{
            min-height: 38px;
            background-color: {BRAND.get('modal_input_bg', colors.get('input_bg', '#FFFFFF'))};
            color: {colors['text_primary']};
            border: 1px solid {BRAND.get('modal_input_border', colors.get('border'))};
            border-radius: {radius_md}px;
            padding: 7px 10px;
            font-weight: 820;
        }}
        QDialog[modalVisualPhase="452"] QTableView[visualRole="modal_table"],
        QDialog[modalVisualPhase="452"] QTableWidget[visualRole="modal_table"] {{
            background-color: {colors.get('bg_table', '#FFFFFF')};
            alternate-background-color: {colors.get('bg_table_alt', '#F8FAFC')};
            border: 1px solid {BRAND.get('modal_shell_border', colors.get('border'))};
            border-radius: {radius_md}px;
            gridline-color: {colors.get('border')};
            selection-background-color: {colors.get('selection_bg')};
            selection-color: {colors.get('selection_text')};
        }}
        QDialog[modalVisualPhase="452"] QTableView[visualRole="modal_table"] QHeaderView::section,
        QDialog[modalVisualPhase="452"] QTableWidget[visualRole="modal_table"] QHeaderView::section {{
            background-color: {BRAND.get('modal_table_header_bg', colors.get('brand_soft'))};
            color: {BRAND.get('modal_table_header_text', colors.get('primary'))};
            border: none;
            border-left: 1px solid {BRAND.get('modal_shell_border', colors.get('border'))};
            padding: 8px;
            font-weight: 950;
        }}
        QDialog[modalVisualPhase="452"] QTabWidget[visualRole="modal_tabs"]::pane {{
            border: 1px solid {BRAND.get('modal_shell_border', colors.get('border'))};
            border-radius: {radius_md}px;
            background-color: {BRAND.get('modal_body_bg', colors.get('bg_panel'))};
        }}
        QDialog[modalVisualPhase="452"] QPushButton[visualRole="modal_primary_action"],
        QMessageBox[modalVisualPhase="452"] QPushButton[visualRole="modal_primary_action"] {{
            min-height: {BRAND.get('dialog_action_min_height', 42)}px;
            min-width: {BRAND.get('dialog_primary_min_width', 126)}px;
            background-color: {BRAND.get('modal_primary_bg', colors.get('primary'))};
            color: #FFFFFF;
            border: 1px solid {BRAND.get('modal_primary_bg', colors.get('primary'))};
            border-radius: {radius_md}px;
            padding: 8px 16px;
            font-weight: 950;
        }}
        QDialog[modalVisualPhase="452"] QPushButton[visualRole="modal_primary_action"]:hover,
        QMessageBox[modalVisualPhase="452"] QPushButton[visualRole="modal_primary_action"]:hover {{
            background-color: {BRAND.get('modal_primary_hover', colors.get('primary_hover'))};
        }}
        QDialog[modalVisualPhase="452"] QPushButton[visualRole="modal_secondary_action"],
        QDialog[modalVisualPhase="452"] QPushButton[visualRole="modal_close_action"],
        QMessageBox[modalVisualPhase="452"] QPushButton[visualRole="modal_secondary_action"],
        QMessageBox[modalVisualPhase="452"] QPushButton[visualRole="modal_close_action"] {{
            min-height: {BRAND.get('dialog_action_min_height', 42)}px;
            min-width: {BRAND.get('dialog_action_min_width', 104)}px;
            background-color: {BRAND.get('modal_secondary_bg', '#FFFFFF')};
            color: {BRAND.get('modal_secondary_text', colors.get('text_primary'))};
            border: 1px solid {BRAND.get('modal_shell_border', colors.get('border'))};
            border-radius: {radius_md}px;
            padding: 8px 14px;
            font-weight: 900;
        }}
        QDialog[modalVisualPhase="452"] QPushButton[visualRole="modal_danger_action"],
        QMessageBox[modalVisualPhase="452"] QPushButton[visualRole="modal_danger_action"] {{
            min-height: {BRAND.get('dialog_action_min_height', 42)}px;
            min-width: {BRAND.get('dialog_action_min_width', 104)}px;
            background-color: {BRAND.get('modal_danger_bg', colors.get('danger_soft'))};
            color: {BRAND.get('modal_danger_text', colors.get('danger'))};
            border: 1px solid {BRAND.get('modal_danger_text', colors.get('danger'))};
            border-radius: {radius_md}px;
            padding: 8px 14px;
            font-weight: 900;
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
            --arj-brand-ink: {colors.get('brand_ink', colors['text_primary'])};
            --arj-brand-navy: {colors.get('brand_navy', colors['primary'])};
            --arj-brand-blue: {colors.get('brand_blue', colors['primary'])};
            --arj-brand-teal: {colors.get('brand_teal', colors['accent'])};
            --arj-brand-gold: {colors.get('brand_gold', colors['warning'])};
            --arj-brand-sand: {colors.get('brand_sand', colors['bg_window'])};
        }}
    """
