# -*- coding: utf-8 -*-
"""Language-aware table direction policy.

Tables are data surfaces, so their visual column order must follow the active UI
language instead of inheriting an old hard-coded RTL direction.  Arabic remains
RTL; German, English and French are LTR.
"""
from __future__ import annotations

from typing import Iterable

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView, QTableView, QTableWidget, QWidget

from i18n.translator import normalize_language, qt_layout_direction


def table_layout_direction(lang: str | None = None) -> Qt.LayoutDirection:
    """Return the Qt layout direction used by all table surfaces."""
    return qt_layout_direction(normalize_language(lang) if lang else None)


def _headers_for(table: QAbstractItemView) -> Iterable[QHeaderView]:
    for attr in ("horizontalHeader", "verticalHeader"):
        getter = getattr(table, attr, None)
        if getter is None:
            continue
        try:
            header = getter()
        except Exception:
            header = None
        if header is not None:
            yield header


def apply_table_direction(table: QAbstractItemView | None, lang: str | None = None) -> None:
    """Apply UI-language direction to a QTableView/QTableWidget and headers.

    The table itself, viewport and headers may each hold an explicit Qt layout
    direction.  Applying all of them prevents previously RTL-created tables from
    staying reversed after switching to a non-Arabic language at runtime.
    """
    if table is None:
        return
    direction = table_layout_direction(lang)
    try:
        table.setLayoutDirection(direction)
        table.setProperty("language_table_direction", "rtl" if direction == Qt.RightToLeft else "ltr")
    except Exception:
        pass
    try:
        viewport = table.viewport()
        if viewport is not None:
            viewport.setLayoutDirection(direction)
    except Exception:
        pass
    for header in _headers_for(table):
        try:
            header.setLayoutDirection(direction)
        except Exception:
            pass
    try:
        table.updateGeometry()
        table.viewport().update()
        table.update()
    except Exception:
        pass


def apply_table_direction_tree(root: QWidget | None, lang: str | None = None) -> None:
    """Apply table direction to every table under a widget tree."""
    if root is None:
        return
    if isinstance(root, (QTableView, QTableWidget)):
        apply_table_direction(root, lang)
    tables = []
    try:
        tables.extend(root.findChildren(QTableView))
    except Exception:
        pass
    try:
        tables.extend(root.findChildren(QTableWidget))
    except Exception:
        pass
    seen = set()
    for table in tables:
        ident = id(table)
        if ident in seen:
            continue
        seen.add(ident)
        apply_table_direction(table, lang)


__all__ = ["apply_table_direction", "apply_table_direction_tree", "table_layout_direction"]
