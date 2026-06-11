# -*- coding: utf-8 -*-
"""Runtime Qt text localization helpers.

This module intentionally translates only visible, user-facing text and leaves
numbers, codes, paths, SQL/table identifiers and object names untouched.
It is safe to call repeatedly from showEvent/refresh paths.
"""
from __future__ import annotations

import re
from typing import Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QToolButton, QCheckBox, QRadioButton,
    QGroupBox, QLineEdit, QComboBox, QTabWidget, QTableView, QMenuBar,
    QMenu, QAction, QDialogButtonBox
)

from .translator import translate_text, is_rtl

_ICON_PREFIX_RE = re.compile(r'^(?:[\U0001F300-\U0001FAFF\u2600-\u27BF]+\s*)+')


def _localize_text(text: Any) -> str:
    if text is None:
        return ''
    raw = str(text)
    if not raw.strip():
        return raw
    # Preserve emoji/icon prefixes used in buttons/menus.
    m = _ICON_PREFIX_RE.match(raw)
    prefix = m.group(0) if m else ''
    rest = raw[len(prefix):].strip() if prefix else raw.strip()
    translated = translate_text(rest)
    return (prefix + translated) if prefix else translated


def apply_widget_language(root: QWidget) -> None:
    """Localize visible texts in a widget tree according to current language."""
    if root is None:
        return
    try:
        root.setLayoutDirection(Qt.RightToLeft if is_rtl() else Qt.LeftToRight)
    except Exception:
        pass

    widgets = [root] + list(root.findChildren(QWidget))
    for w in widgets:
        try:
            if isinstance(w, (QLabel, QPushButton, QToolButton, QCheckBox, QRadioButton, QGroupBox)):
                txt = w.text()
                new = _localize_text(txt)
                if new != txt:
                    w.setText(new)
            if isinstance(w, QLineEdit):
                ph = w.placeholderText()
                new = _localize_text(ph)
                if new != ph:
                    w.setPlaceholderText(new)
            if isinstance(w, QComboBox):
                for i in range(w.count()):
                    txt = w.itemText(i)
                    new = _localize_text(txt)
                    if new != txt:
                        w.setItemText(i, new)
            if isinstance(w, QTabWidget):
                for i in range(w.count()):
                    txt = w.tabText(i)
                    new = _localize_text(txt)
                    if new != txt:
                        w.setTabText(i, new)
            if isinstance(w, QTableView) and w.model():
                try:
                    w.model().headerDataChanged.emit(Qt.Horizontal, 0, max(0, w.model().columnCount() - 1))
                except Exception:
                    pass
        except RuntimeError:
            continue
        except Exception:
            continue

    # Menus/actions are not QWidget children in all cases.
    for action in root.findChildren(QAction):
        try:
            txt = action.text()
            new = _localize_text(txt)
            if new != txt:
                action.setText(new)
            tip = action.toolTip()
            new_tip = _localize_text(tip)
            if new_tip != tip:
                action.setToolTip(new_tip)
        except Exception:
            pass


def localize_action_text(text: Any) -> str:
    return _localize_text(text)
