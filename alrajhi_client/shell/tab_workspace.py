# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import qtawesome as qta
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QTabWidget, QWidget

from i18n.translator import translate


class TabbedWorkspace(QTabWidget):
    """ERP workspace built on internal tabs instead of one-page-at-a-time windows.

    The class intentionally keeps a tiny compatibility surface with QStackedWidget
    (`currentWidget`, `setCurrentWidget`) so the legacy MainWindow can migrate in
    phases without rewriting every page at once.
    """

    currentPageChanged = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("TabbedWorkspace")
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self._tab_ids: Dict[str, QWidget] = {}
        self._widget_ids: Dict[QWidget, str] = {}
        self._dirty: Dict[str, bool] = {}
        self._meta: Dict[str, Tuple[str, str, bool]] = {}
        self.tabCloseRequested.connect(self.close_tab_at)
        self.currentChanged.connect(self._emit_current_page)
        self.setStyleSheet(
            """
            QTabWidget::pane {
                border: 1px solid palette(mid);
                border-top: none;
                background: palette(base);
            }
            QTabBar::tab {
                min-height: 30px;
                padding: 7px 14px;
                margin: 0 1px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                background: palette(window);
                color: palette(text);
                font-weight: 700;
            }
            QTabBar::tab:selected {
                background: palette(base);
                border: 1px solid palette(mid);
                border-bottom-color: palette(base);
            }
            QTabBar::tab:hover:!selected { background: palette(alternate-base); }
            """
        )

    def addWidget(self, widget: QWidget) -> int:  # compatibility with old stack usage
        return self.open_tab(widget.objectName() or f"page_{id(widget)}", widget.windowTitle() or "", widget)

    def open_tab(self, tab_id: str, title: str, widget: QWidget, icon_name: str = "fa5s.folder-open", singleton: bool = True) -> int:
        if singleton and tab_id in self._tab_ids:
            self.setCurrentWidget(self._tab_ids[tab_id])
            return self.currentIndex()
        title = title or tab_id
        icon = qta.icon(icon_name) if icon_name else qta.icon("fa5s.folder-open")
        index = self.addTab(widget, icon, title)
        self._tab_ids[tab_id] = widget
        self._widget_ids[widget] = tab_id
        self._dirty[tab_id] = False
        self._meta[tab_id] = (title, icon_name, bool(singleton))
        self.setCurrentIndex(index)
        return index

    def open_singleton(self, tab_id: str, title: str, widget: QWidget, icon_name: str = "fa5s.folder-open") -> int:
        return self.open_tab(tab_id, title, widget, icon_name=icon_name, singleton=True)

    def mark_dirty(self, tab_id: str, dirty: bool = True) -> None:
        widget = self._tab_ids.get(tab_id)
        if widget is None:
            return
        self._dirty[tab_id] = bool(dirty)
        index = self.indexOf(widget)
        if index >= 0:
            base_title = self.tabText(index).rstrip(" *")
            self.setTabText(index, f"{base_title} *" if dirty else base_title)

    def is_dirty(self, tab_id: str) -> bool:
        return bool(self._dirty.get(tab_id))

    def close_tab_at(self, index: int) -> bool:
        widget = self.widget(index)
        if widget is None:
            return False
        tab_id = self._widget_ids.get(widget, "")
        if hasattr(widget, 'can_close') and not widget.can_close():
            return False
        if tab_id and self._dirty.get(tab_id):
            reply = QMessageBox.question(
                self,
                translate("workspace.unsaved_title"),
                translate("workspace.unsaved_close"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return False
        self.removeTab(index)
        if tab_id:
            self._tab_ids.pop(tab_id, None)
            self._dirty.pop(tab_id, None)
            self._meta.pop(tab_id, None)
        self._widget_ids.pop(widget, None)
        widget.setParent(None)
        return True

    def close_current_tab(self) -> bool:
        index = self.currentIndex()
        return False if index < 0 else self.close_tab_at(index)


    def open_tab_ids(self) -> List[str]:
        return [self._widget_ids.get(self.widget(index), "") for index in range(self.count()) if self.widget(index) is not None]

    def tab_entry_data(self) -> List[Tuple[str, str, str, bool]]:
        entries: List[Tuple[str, str, str, bool]] = []
        for tab_id in self.open_tab_ids():
            if not tab_id:
                continue
            title, icon_name, singleton = self._meta.get(tab_id, (tab_id, "fa5s.folder-open", True))
            entries.append((tab_id, title, icon_name, singleton))
        return entries

    def setCurrentWidget(self, widget: QWidget) -> None:  # type: ignore[override]
        index = self.indexOf(widget)
        if index >= 0:
            self.setCurrentIndex(index)

    def current_page_id(self) -> Optional[str]:
        return self._widget_ids.get(self.currentWidget())

    def _emit_current_page(self, _index: int) -> None:
        page_id = self.current_page_id()
        if page_id:
            self.currentPageChanged.emit(page_id)
