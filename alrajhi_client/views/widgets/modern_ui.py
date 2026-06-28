# -*- coding: utf-8 -*-
"""Shared visual helpers for Alrajhi desktop pages and dialogs.

The helpers intentionally avoid business logic. They only normalize spacing,
headers, card-like surfaces, controls, and tables so legacy pages can gradually
match the invoice/material visual language without a risky rewrite.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QFrame, QHBoxLayout, QVBoxLayout, QLayout, QTableView, QTableWidget, QPushButton, QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QGroupBox, QTabWidget, QDialogButtonBox
from theme_manager import ThemeManager
from ui.dialog_branding import apply_branded_dialog, normalize_dialog_buttons
from i18n.translator import qt_layout_direction
from ui.table_direction_policy import apply_table_direction


def _modern_widget_style() -> str:
    """Return page/dialog QSS from the active Al Rajhi Design System tokens.

    This replaces the former hard-coded blue/gray stylesheet while keeping the
    same safe per-page application model: no global event filter and no runtime
    mutation of newly created widgets.
    """
    c = ThemeManager.colors()
    return f"""
QWidget {{
    background: {c['bg_window']};
    color: {c['text_primary']};
    font-size: 13px;
}}
QFrame#ModernPageHeader, QFrame#ModernSectionCard {{
    background: {c['card_bg']};
    border: 1px solid {c['border']};
    border-radius: 12px;
}}
QLabel#ModernPageTitle {{
    font-size: 20px;
    font-weight: 800;
    color: {c['primary']};
    background: transparent;
}}
QLabel#ModernPageSubtitle, QLabel#muted, QLabel[muted="true"] {{
    color: {c['text_secondary']};
    background: transparent;
}}

QLabel#ModernInfoBox, QLabel#ModernSummaryBox {{
    background: {c['brand_soft']};
    color: {c['text_secondary']};
    border: 1px solid {c['border']};
    border-radius: 10px;
    padding: 10px;
    font-weight: 700;
}}
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {{
    background: {c['input_bg']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 9px;
    padding: 7px 10px;
    min-height: 30px;
    selection-background-color: {c['selection_bg']};
    selection-color: {c['selection_text']};
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
    border: 1px solid {c['border_focus']};
}}
QPushButton {{
    background: {c['bg_panel']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 9px;
    padding: 7px 14px;
    min-height: 30px;
    font-weight: 700;
}}
QPushButton:hover {{ background: {c['brand_soft']}; border-color: {c['primary']}; }}
QPushButton:disabled {{ color: {c['text_muted']}; background: {c['bg_window']}; }}
QPushButton#primary {{
    background: {c['primary']};
    border-color: {c['primary']};
    color: #ffffff;
}}
QPushButton#primary:hover {{ background: {c['primary_hover']}; }}
QPushButton#danger {{
    background: {c['danger_soft']};
    border-color: {c['danger']};
    color: {c['danger']};
}}
QTableView, QTableWidget, QTreeView, QTreeWidget {{
    background: {c['bg_table']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 12px;
    gridline-color: {c['border']};
    alternate-background-color: {c['bg_table_alt']};
    selection-background-color: {c['selection_bg']};
    selection-color: {c['selection_text']};
    outline: 0;
}}
QTableView::item, QTableWidget::item, QTreeView::item, QTreeWidget::item {{
    padding: 6px;
    border-bottom: 1px solid {c['border']};
}}
QTableView::item:hover, QTableWidget::item:hover, QTreeView::item:hover, QTreeWidget::item:hover {{
    background: {c['brand_soft']};
}}
QHeaderView::section {{
    background: {c['header_bg']};
    color: {c['header_text']};
    padding: 8px;
    border: 0;
    border-left: 1px solid {c['border']};
    font-weight: 800;
}}
QTabWidget::pane {{
    border: 1px solid {c['border']};
    border-radius: 12px;
    background: {c['bg_window']};
    top: -1px;
}}
QTabWidget QWidget {{
    background: {c['bg_window']};
    color: {c['text_primary']};
}}
QTabBar::tab {{
    background: {c['bg_panel']};
    color: {c['text_secondary']};
    border: 1px solid {c['border']};
    padding: 9px 18px;
    margin-left: 4px;
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
    font-weight: 700;
}}
QTabBar::tab:hover {{ background: {c['brand_soft']}; color: {c['primary']}; }}
QTabBar::tab:selected {{
    background: {c['primary']};
    color: #ffffff;
}}
QGroupBox {{
    background: {c['card_bg']};
    border: 1px solid {c['border']};
    border-radius: 12px;
    margin-top: 12px;
    padding: 12px;
    font-weight: 800;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    right: 14px;
    padding: 0 6px;
    color: {c['primary']};
    background: {c['card_bg']};
}}
QFrame#ModernToolbar, QFrame#ModernActionBar {{
    background: {c['card_bg']};
    border: 1px solid {c['border']};
    border-radius: 12px;
}}
QDialogButtonBox QPushButton {{
    min-width: 92px;
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
"""


def _normalize_layout(layout: QLayout):
    if layout is None:
        return
    try:
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)
    except Exception:
        pass


def _make_header(title: str, subtitle: str = '') -> QFrame:
    header = QFrame()
    header.setObjectName('ModernPageHeader')
    box = QHBoxLayout(header)
    box.setContentsMargins(16, 14, 16, 14)
    box.setSpacing(8)
    texts = QVBoxLayout()
    texts.setContentsMargins(0, 0, 0, 0)
    title_label = QLabel(title)
    title_label.setObjectName('ModernPageTitle')
    texts.addWidget(title_label)
    if subtitle:
        sub = QLabel(subtitle)
        sub.setObjectName('ModernPageSubtitle')
        texts.addWidget(sub)
    box.addLayout(texts, 1)
    return header



def _walk_widgets(widget):
    widgets = []
    for cls in (QTableView, QTableWidget, QPushButton, QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QGroupBox, QTabWidget, QDialogButtonBox):
        try:
            widgets.extend(widget.findChildren(cls))
        except Exception:
            pass
    seen = set()
    ordered = []
    for child in widgets:
        ident = id(child)
        if ident in seen:
            continue
        seen.add(ident)
        ordered.append(child)
    return ordered

def _normalize_child_controls(widget):
    for child in _walk_widgets(widget):
        try:
            if isinstance(child, (QTableView, QTableWidget)):
                apply_table_direction(child)
                child.setAlternatingRowColors(True)
                child.setShowGrid(False)
                if hasattr(child, 'verticalHeader'):
                    child.verticalHeader().setDefaultSectionSize(34)
                if hasattr(child, 'horizontalHeader'):
                    child.horizontalHeader().setStretchLastSection(True)
            elif isinstance(child, (QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox)):
                child.setMinimumHeight(36)
            elif isinstance(child, QTextEdit):
                child.setMinimumHeight(max(child.minimumHeight(), 82))
            elif isinstance(child, QPushButton):
                child.setMinimumHeight(34)
                text = child.text() or ''
                if any(key in text for key in ('حفظ', 'إضافة', 'جديد', 'إنشاء')) and child.objectName() == '':
                    child.setObjectName('primary')
                if any(key in text for key in ('حذف', 'أرشفة', 'إلغاء')) and child.objectName() == '':
                    child.setObjectName('danger' if 'حذف' in text or 'أرشفة' in text else '')
        except Exception:
            pass

def make_section_card(title: str = '') -> QGroupBox:
    card = QGroupBox(title)
    card.setObjectName('ModernSectionCard')
    return card


def _apply_basit_list_surface(widget):
    """Phase404: give management/list workspaces the Basit operational surface.

    This is intentionally property-based: business widgets keep their existing
    logic, while QSS centralizes the visual grammar.
    """
    try:
        if not any(hasattr(widget, name) for name in ('table', 'cash_table', 'bank_table', 'search_edit')):
            return
        widget.setProperty('basitInspired', True)
        widget.setProperty('basitManagementWorkspace', True)
    except Exception:
        pass
    for name in ('search_edit', 'cash_search', 'bank_search', 'voucher_type_filter'):
        ctrl = getattr(widget, name, None)
        if ctrl is not None:
            try:
                ctrl.setProperty('basitListSearch', True)
            except Exception:
                pass
    for name in ('add_btn', 'edit_btn', 'delete_btn', 'print_btn', 'export_btn', 'refresh_btn', 'prev_btn', 'next_btn', 'batch_print_btn', 'print_barcode_btn'):
        btn = getattr(widget, name, None)
        if btn is not None:
            try:
                btn.setProperty('basitToolbarButton', True)
            except Exception:
                pass
    for table_name in ('table', 'cash_table', 'bank_table', 'shift_table', 'mov_table', 'bom_table', 'orders_table'):
        table = getattr(widget, table_name, None)
        if table is not None:
            try:
                table.setProperty('basitTable', True)
                table.setProperty('basitManagementTable', True)
            except Exception:
                pass


def apply_modern_widget(widget, title: str = '', subtitle: str = ''):
    """Apply the unified page visual language to an existing QWidget page."""
    widget.setLayoutDirection(qt_layout_direction())
    current = widget.styleSheet() or ''
    if 'ModernPageHeader' not in current:
        widget.setStyleSheet(current + '\n' + _modern_widget_style())
    layout = widget.layout()
    _normalize_layout(layout)
    # Phase118: page-level explanatory/header cards are intentionally disabled
    # across all widgets. Navigation/context already provides the page title, and
    # adding per-page header cards made the UI inconsistent. Keep styling and
    # control normalization only; also remove any legacy ModernPageHeader that
    # may have been inserted by older versions.
    if layout is not None:
        try:
            for idx in reversed(range(layout.count())):
                item = layout.itemAt(idx)
                child = item.widget() if item else None
                if child is not None and child.objectName() == 'ModernPageHeader':
                    layout.removeWidget(child)
                    child.deleteLater()
        except Exception:
            pass
    _normalize_child_controls(widget)
    _apply_basit_list_surface(widget)
    for table_name in ('table', 'cash_table', 'bank_table', 'shift_table', 'mov_table', 'bom_table', 'orders_table'):
        table = getattr(widget, table_name, None)
        if table is not None:
            try:
                apply_table_direction(table)
                table.setAlternatingRowColors(True)
                table.verticalHeader().setDefaultSectionSize(34)
                table.setShowGrid(False)
            except Exception:
                pass
    for name in ('search_edit', 'cash_search', 'bank_search', 'voucher_type_filter'):
        ctrl = getattr(widget, name, None)
        if ctrl is not None:
            try:
                ctrl.setMinimumHeight(36)
            except Exception:
                pass


def apply_modern_dialog(dialog, title: str = ''):
    """Apply the unified dialog visual language.

    Phase356 delegates final object names, button roles and system-window QSS
    hooks to ``apply_branded_dialog`` so legacy dialogs, picker windows and
    modern dialogs share one branded identity.
    """
    dialog.setLayoutDirection(qt_layout_direction())
    current = dialog.styleSheet() or ''
    if 'ModernPageHeader' not in current:
        dialog.setStyleSheet(current + '\n' + _modern_widget_style())
    try:
        dialog.resize(max(dialog.width(), 560), max(dialog.height(), 380))
    except Exception:
        pass
    container = getattr(dialog, 'content_widget', dialog)
    layout = container.layout() if hasattr(container, 'layout') else None
    _normalize_layout(layout)
    if title and layout is not None:
        try:
            first = layout.itemAt(0).widget() if layout.count() else None
            if not (first and first.objectName() in ('ModernPageHeader', 'BrandDialogHeaderCard')):
                header = _make_header(title)
                header.setObjectName('BrandDialogHeaderCard')
                header.setProperty('dialogSurface', 'headerCard')
                layout.insertWidget(0, header)
        except Exception:
            pass
    _normalize_child_controls(dialog)
    normalize_dialog_buttons(dialog)
    apply_branded_dialog(dialog, title, role='modern')

