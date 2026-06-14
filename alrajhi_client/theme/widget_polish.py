# -*- coding: utf-8 -*-
"""Runtime UI polish for tables and tabs.

This module guarantees that tables/tabs created in any page, dialog, or lazy
loaded widget inherit the Al Rajhi design-system behavior even when they are
created after the application stylesheet is applied.
"""
from __future__ import annotations

try:
    from PyQt5.QtCore import QObject, QEvent, Qt
    from PyQt5.QtWidgets import (
        QApplication, QAbstractItemView, QHeaderView, QTableView, QTableWidget,
        QTreeView, QTreeWidget, QTabWidget
    )
except Exception:  # pragma: no cover - keeps import safe in non-Qt tooling
    QObject = object
    QEvent = None
    Qt = None
    QApplication = None
    QAbstractItemView = None
    QHeaderView = None
    QTableView = QTableWidget = QTreeView = QTreeWidget = QTabWidget = ()

_TABLE_TYPES = (QTableView, QTableWidget, QTreeView, QTreeWidget)


def _already_polished(widget) -> bool:
    try:
        return bool(widget.property('_arjDesignSystemPolished'))
    except Exception:
        return False


def _mark_polished(widget):
    try:
        widget.setProperty('_arjDesignSystemPolished', True)
    except Exception:
        pass


def polish_table(table):
    """Apply behavior-level defaults that QSS alone cannot enforce."""
    if table is None or _already_polished(table):
        return
    try:
        table.setAlternatingRowColors(True)
    except Exception:
        pass
    try:
        table.setShowGrid(False)
    except Exception:
        pass
    try:
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
    except Exception:
        pass
    try:
        table.setSelectionMode(QAbstractItemView.SingleSelection)
    except Exception:
        pass
    try:
        table.setWordWrap(False)
    except Exception:
        pass
    try:
        table.setSortingEnabled(False)  # keep legacy data-loading semantics stable
    except Exception:
        pass
    try:
        table.setObjectName(table.objectName() or 'arjTable')
    except Exception:
        pass
    try:
        vh = table.verticalHeader()
        vh.setDefaultSectionSize(34)
        vh.setVisible(False)
    except Exception:
        pass
    try:
        hh = table.horizontalHeader()
        hh.setDefaultAlignment(Qt.AlignCenter)
        hh.setMinimumSectionSize(78)
        hh.setHighlightSections(False)
        hh.setStretchLastSection(True)
        # Keep user/application-defined resize modes; only use interactive if unset.
    except Exception:
        pass
    _mark_polished(table)


def polish_tab_widget(tabs):
    if tabs is None or _already_polished(tabs):
        return
    try:
        tabs.setObjectName(tabs.objectName() or 'arjTabs')
        tabs.setDocumentMode(False)
        tabs.setUsesScrollButtons(True)
        tabs.setMovable(False)
    except Exception:
        pass
    _mark_polished(tabs)


def polish_widget_tree(widget):
    if widget is None:
        return
    try:
        if isinstance(widget, _TABLE_TYPES):
            polish_table(widget)
        elif isinstance(widget, QTabWidget):
            polish_tab_widget(widget)
    except Exception:
        pass
    try:
        for table in widget.findChildren(_TABLE_TYPES):
            polish_table(table)
        for tabs in widget.findChildren(QTabWidget):
            polish_tab_widget(tabs)
    except Exception:
        pass


class _DesignSystemEventFilter(QObject):
    def eventFilter(self, obj, event):  # noqa: N802 - Qt API
        try:
            if event is not None and event.type() in (QEvent.Show, QEvent.ChildAdded, QEvent.Polish):
                polish_widget_tree(obj)
        except Exception:
            pass
        return False


_filter = None


def install_design_system_polish(app=None):
    """Install a process-wide filter for tables/tabs and polish current widgets."""
    global _filter
    if QApplication is None:
        return None
    app = app or QApplication.instance()
    if app is None:
        return None
    if _filter is None:
        _filter = _DesignSystemEventFilter(app)
        app.installEventFilter(_filter)
    try:
        for widget in app.allWidgets():
            polish_widget_tree(widget)
    except Exception:
        pass
    return _filter
