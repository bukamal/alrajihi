# -*- coding: utf-8 -*-
"""Shared visual helpers for Alrajhi desktop pages and dialogs.

The helpers intentionally avoid business logic. They only normalize spacing,
headers, card-like surfaces, controls, and tables so legacy pages can gradually
match the invoice/material visual language without a risky rewrite.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QFrame, QHBoxLayout, QVBoxLayout, QLayout, QTableView, QTableWidget, QPushButton, QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QGroupBox, QTabWidget, QDialogButtonBox


_MODERN_WIDGET_STYLE = """
QWidget {
    background: #f6f8fb;
    color: #172033;
    font-size: 13px;
}
QFrame#ModernPageHeader, QFrame#ModernSectionCard {
    background: #ffffff;
    border: 1px solid #dfe5ef;
    border-radius: 12px;
}
QLabel#ModernPageTitle {
    font-size: 20px;
    font-weight: 700;
    color: #0f172a;
    background: transparent;
}
QLabel#ModernPageSubtitle, QLabel#muted, QLabel[muted="true"] {
    color: #64748b;
    background: transparent;
}
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    background: #ffffff;
    border: 1px solid #cfd8e6;
    border-radius: 9px;
    padding: 7px 10px;
    min-height: 30px;
    selection-background-color: #2563eb;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
    border: 1px solid #2563eb;
}
QPushButton {
    background: #ffffff;
    border: 1px solid #cfd8e6;
    border-radius: 9px;
    padding: 7px 14px;
    min-height: 30px;
    font-weight: 600;
}
QPushButton:hover { background: #f1f5f9; }
QPushButton:disabled { color: #94a3b8; background: #f8fafc; }
QPushButton#primary {
    background: #2563eb;
    border-color: #2563eb;
    color: #ffffff;
}
QPushButton#primary:hover { background: #1d4ed8; }
QPushButton#danger {
    background: #fee2e2;
    border-color: #fecaca;
    color: #b91c1c;
}
QTableView, QTableWidget {
    background: #ffffff;
    border: 1px solid #dfe5ef;
    border-radius: 12px;
    gridline-color: #e5e7eb;
    alternate-background-color: #f8fafc;
    selection-background-color: #dbeafe;
    selection-color: #0f172a;
}
QHeaderView::section {
    background: #eef2f7;
    color: #172033;
    padding: 8px;
    border: 0;
    border-left: 1px solid #dfe5ef;
    font-weight: 700;
}
QTabWidget::pane {
    border: 1px solid #dfe5ef;
    border-radius: 12px;
    background: #ffffff;
    top: -1px;
}
QTabBar::tab {
    background: #eef2f7;
    border: 1px solid #dfe5ef;
    padding: 9px 18px;
    margin-left: 4px;
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #2563eb;
}
QGroupBox {
    background: #ffffff;
    border: 1px solid #dfe5ef;
    border-radius: 12px;
    margin-top: 12px;
    padding: 12px;
    font-weight: 700;
}
QGroupBox::title {
    subcontrol-origin: margin;
    right: 14px;
    padding: 0 6px;
    color: #0f172a;
}
QFrame#ModernToolbar, QFrame#ModernActionBar {
    background: #ffffff;
    border: 1px solid #dfe5ef;
    border-radius: 12px;
}
QDialogButtonBox QPushButton {
    min-width: 92px;
}
QScrollArea {
    border: none;
    background: transparent;
}
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
    try:
        return widget.findChildren((QTableView, QTableWidget, QPushButton, QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QGroupBox, QTabWidget, QDialogButtonBox))
    except Exception:
        return []

def _normalize_child_controls(widget):
    for child in _walk_widgets(widget):
        try:
            if isinstance(child, (QTableView, QTableWidget)):
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

def apply_modern_widget(widget, title: str = '', subtitle: str = ''):
    """Apply the unified page visual language to an existing QWidget page."""
    widget.setLayoutDirection(Qt.RightToLeft)
    current = widget.styleSheet() or ''
    if 'ModernPageHeader' not in current:
        widget.setStyleSheet(current + '\n' + _MODERN_WIDGET_STYLE)
    layout = widget.layout()
    _normalize_layout(layout)
    if title and layout is not None:
        try:
            first = layout.itemAt(0).widget() if layout.count() else None
            if not (first and first.objectName() == 'ModernPageHeader'):
                layout.insertWidget(0, _make_header(title, subtitle))
        except Exception:
            pass
    _normalize_child_controls(widget)
    for table_name in ('table', 'cash_table', 'bank_table', 'shift_table', 'mov_table', 'bom_table', 'orders_table'):
        table = getattr(widget, table_name, None)
        if table is not None:
            try:
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
    """Apply the unified dialog visual language."""
    dialog.setLayoutDirection(Qt.RightToLeft)
    current = dialog.styleSheet() or ''
    if 'ModernPageHeader' not in current:
        dialog.setStyleSheet(current + '\n' + _MODERN_WIDGET_STYLE)
    try:
        dialog.resize(max(dialog.width(), 520), max(dialog.height(), 360))
    except Exception:
        pass
    container = getattr(dialog, 'content_widget', dialog)
    layout = container.layout() if hasattr(container, 'layout') else None
    _normalize_layout(layout)
    if title and layout is not None:
        try:
            first = layout.itemAt(0).widget() if layout.count() else None
            if not (first and first.objectName() == 'ModernPageHeader'):
                layout.insertWidget(0, _make_header(title))
        except Exception:
            pass
    _normalize_child_controls(dialog)
