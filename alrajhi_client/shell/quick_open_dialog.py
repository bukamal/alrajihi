# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

import qtawesome as qta
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout

from i18n.translator import translate


@dataclass(frozen=True)
class QuickOpenItem:
    key: str
    title: str
    subtitle: str = ""
    icon_name: str = "fa5s.folder-open"
    payload: object = None


class QuickOpenDialog(QDialog):
    """Keyboard-first tab launcher for registered workspace pages."""

    def __init__(self, items: Iterable[QuickOpenItem], parent=None, search_provider: Optional[Callable[[str], Iterable[QuickOpenItem]]] = None) -> None:
        super().__init__(parent)
        self.setObjectName("QuickOpenDialog")
        self.setWindowTitle(translate("workspace.quick_open"))
        self.setModal(True)
        self.resize(560, 460)
        self._items: List[QuickOpenItem] = list(items)
        self._selected: Optional[QuickOpenItem] = None
        self._search_provider = search_provider

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        header = QLabel(translate("workspace.quick_open_hint"), self)
        header.setObjectName("QuickOpenHint")
        layout.addWidget(header)

        self.search = QLineEdit(self)
        self.search.setObjectName("QuickOpenSearch")
        self.search.setPlaceholderText(translate("workspace.quick_open_placeholder"))
        layout.addWidget(self.search)

        self.list_widget = QListWidget(self)
        self.list_widget.setObjectName("QuickOpenList")
        layout.addWidget(self.list_widget, 1)

        footer_row = QHBoxLayout()
        footer = QLabel(translate("workspace.quick_open_footer"), self)
        footer.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        footer_row.addWidget(footer)
        layout.addLayout(footer_row)

        self.search.textChanged.connect(self._filter)
        self.search.returnPressed.connect(self._accept_current)
        self.list_widget.itemDoubleClicked.connect(lambda _item: self._accept_current())
        self._filter("")

        self.setStyleSheet(
            """
            QDialog#QuickOpenDialog { background: palette(base); }
            QLabel#QuickOpenHint { font-size: 13px; font-weight: 700; color: palette(text); }
            QLineEdit#QuickOpenSearch { min-height: 34px; padding: 6px 10px; font-size: 14px; border-radius: 8px; border: 1px solid palette(mid); }
            QListWidget#QuickOpenList { border: 1px solid palette(mid); border-radius: 10px; padding: 6px; }
            QListWidget#QuickOpenList::item { padding: 9px 8px; border-radius: 8px; }
            QListWidget#QuickOpenList::item:selected { background: palette(highlight); color: palette(highlighted-text); }
            """
        )

    def selected_item(self) -> Optional[QuickOpenItem]:
        return self._selected

    def _filter(self, text: str) -> None:
        raw_text = text or ""
        needle = raw_text.strip().casefold()
        self.list_widget.clear()
        filtered: List[QuickOpenItem] = []
        for item in self._items:
            haystack = f"{item.key} {item.title} {item.subtitle}".casefold()
            if needle and needle not in haystack:
                continue
            filtered.append(item)
        if self._search_provider and len(needle) >= 2:
            try:
                filtered.extend(list(self._search_provider(raw_text)))
            except Exception:
                pass
        seen = set()
        for item in filtered:
            marker = (item.key, item.title)
            if marker in seen:
                continue
            seen.add(marker)
            row = QListWidgetItem(qta.icon(item.icon_name), item.title)
            if item.subtitle:
                row.setToolTip(item.subtitle)
            row.setData(Qt.UserRole, item)
            self.list_widget.addItem(row)
        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)

    def _accept_current(self) -> None:
        item = self.list_widget.currentItem()
        if item is None:
            return
        value = item.data(Qt.UserRole)
        if isinstance(value, QuickOpenItem):
            self._selected = value
            self.accept()
