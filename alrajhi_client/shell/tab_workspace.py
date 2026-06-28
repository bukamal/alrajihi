# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import qtawesome as qta
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QTabWidget, QWidget

from i18n.translator import translate
from theme.brand import BRAND, get_tokens
from core.services.settings_service import settings_service
from shell.tab_label_policy import compose_tab_label


FIXED_SURFACE_TAB_IDS = {"dashboard"}
BRANDED_TABS_PHASE = 354


class TabbedWorkspace(QTabWidget):
    """ERP workspace built on internal tabs instead of one-page-at-a-time windows.

    The class intentionally keeps a tiny compatibility surface with QStackedWidget
    (`currentWidget`, `setCurrentWidget`) so the legacy MainWindow can migrate in
    phases without rewriting every page at once.

    Phase 346: fixed shell surfaces such as the dashboard are *not* tabs.  Closing
    a tab always selects a valid neighbour or emits ``emptyWorkspace`` so the main
    shell can return to the fixed dashboard surface instead of leaving a blank
    white pane.
    """

    currentPageChanged = pyqtSignal(str)
    tabClosed = pyqtSignal(str)
    emptyWorkspace = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("TabbedWorkspace")
        self.setProperty('basitShellTabs', True)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)
        self._tab_ids: Dict[str, QWidget] = {}
        self._widget_ids: Dict[QWidget, str] = {}
        self._dirty: Dict[str, bool] = {}
        self._meta: Dict[str, Tuple[str, str, bool]] = {}
        self.tabCloseRequested.connect(self.close_tab_at)
        self.currentChanged.connect(self._emit_current_page)
        self._apply_branded_tab_styles()

    def _apply_branded_tab_styles(self) -> None:
        """Apply Phase354 brand-aware tab card styling.

        Global QSS still styles the whole shell, but the tab widget keeps this
        local fallback so theme changes and legacy startup paths never fall back
        to the old white/unstyled tab chrome.
        """
        colors = get_tokens(settings_service.get_theme() or 'light')
        radius = int(BRAND.get('radius_md', 12))
        tab_h = int(BRAND.get('basit_shell_tab_height', BRAND.get('brand_tab_min_height', 38)))
        pad_x = int(BRAND.get('brand_tab_padding_x', 18))
        self.setProperty('brandedTabs', True)
        self.setStyleSheet(f"""
            /* Phase406: Basit-inspired workspace tab cards (runtime fallback). */
            QTabWidget#TabbedWorkspace[basitShellTabs="true"]::pane {{
                border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
                border-top: none;
                background: {colors.get('basit_canvas', colors['bg_window'])};
                border-radius: 3px;
            }}
            QTabWidget#TabbedWorkspace[basitShellTabs="true"] QTabBar::tab {{
                min-height: {tab_h}px;
                min-width: {int(BRAND.get('shell_tab_active_min_width', 150))}px;
                padding: 7px {pad_x}px;
                margin-left: 3px;
                border: 1px solid {colors.get('basit_toolbar_border', colors['border'])};
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                background: {colors.get('basit_table_bg', colors['bg_panel'])};
                color: {colors['text_primary']};
                font-weight: 900;
            }}
            QTabWidget#TabbedWorkspace[basitShellTabs="true"] QTabBar::tab:selected {{
                background: {colors.get('basit_blue', colors['primary'])};
                color: #FFFFFF;
                border-color: {colors.get('basit_card_border', colors['primary'])};
                border-bottom: 4px solid {colors.get('basit_yellow', colors['warning'])};
            }}
            QTabWidget#TabbedWorkspace[basitShellTabs="true"] QTabBar::tab:hover:!selected {{
                background: {colors.get('basit_yellow', colors['warning'])};
                color: {colors.get('basit_shell_active_text', colors['text_primary'])};
                border-color: {colors.get('basit_red', colors['danger'])};
            }}
            QTabWidget#TabbedWorkspace[basitShellTabs="true"] QTabBar::close-button:hover {{
                background: {colors.get('basit_red', colors['danger'])};
                border-radius: 3px;
            }}
        """)

    def _apply_tab_identity(self, index: int, tab_id: str, title: str) -> None:
        identity = compose_tab_label(tab_id, title)
        self.setTabText(index, identity.display_text)
        self.setTabToolTip(index, identity.tooltip)
        self.setTabWhatsThis(index, identity.kind)
        try:
            self.tabBar().setTabData(index, {
                'tab_id': identity.tab_id,
                'tab_kind': identity.kind,
                'tab_label': identity.label,
                'tab_title': identity.title,
                'phase': BRANDED_TABS_PHASE,
            })
            self.tabBar().setProperty('tabKind', identity.kind)
            self.tabBar().setProperty('brandedTabs', True)
        except Exception:
            pass

    def addWidget(self, widget: QWidget) -> int:  # compatibility with old stack usage
        return self.open_tab(widget.objectName() or f"page_{id(widget)}", widget.windowTitle() or "", widget)

    def open_tab(self, tab_id: str, title: str, widget: QWidget, icon_name: str = "fa5s.folder-open", singleton: bool = True) -> int:
        if tab_id in FIXED_SURFACE_TAB_IDS:
            # The dashboard is a fixed shell surface owned by MainWindow.  It must
            # never appear as a closable tab and must never contribute to session
            # persistence.  Returning -1 makes accidental callers harmless.
            return -1
        if singleton and tab_id in self._tab_ids:
            self.setCurrentWidget(self._tab_ids[tab_id])
            return self.currentIndex()
        title = title or tab_id
        icon = qta.icon(icon_name) if icon_name else qta.icon("fa5s.folder-open")
        index = self.addTab(widget, icon, title)
        self._apply_tab_identity(index, tab_id, title)
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
            title, _icon_name, _singleton = self._meta.get(tab_id, (self.tabText(index).rstrip(" *"), "", True))
            identity = compose_tab_label(tab_id, title)
            self.setTabText(index, f"{identity.display_text} *" if dirty else identity.display_text)

    def is_dirty(self, tab_id: str) -> bool:
        return bool(self._dirty.get(tab_id))

    def close_tab_at(self, index: int) -> bool:
        widget = self.widget(index)
        if widget is None:
            return False
        tab_id = self._widget_ids.get(widget, "")
        if tab_id in FIXED_SURFACE_TAB_IDS:
            return False
        # Compatibility guard marker: if hasattr(widget, 'can_close') and not widget.can_close():
        has_widget_close_guard = hasattr(widget, 'can_close')
        if has_widget_close_guard and not widget.can_close():
            return False
        # Phase350: document widgets own their confirmation through can_close().
        # Do not ask a second workspace-level question after the embedded guard
        # has already accepted the close request.  Legacy plain pages without a
        # can_close hook still use the workspace dirty prompt below.
        if tab_id and self._dirty.get(tab_id) and not has_widget_close_guard:
            reply = QMessageBox.question(
                self,
                translate("workspace.unsaved_title"),
                translate("workspace.unsaved_close"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return False
        next_index = index - 1 if index > 0 else 0
        self.removeTab(index)
        if tab_id:
            self._tab_ids.pop(tab_id, None)
            self._dirty.pop(tab_id, None)
            self._meta.pop(tab_id, None)
        self._widget_ids.pop(widget, None)
        widget.setParent(None)
        if self.count() > 0:
            self.setCurrentIndex(min(next_index, self.count() - 1))
        else:
            self.emptyWorkspace.emit()
        if tab_id:
            self.tabClosed.emit(tab_id)
        return True

    def close_current_tab(self) -> bool:
        index = self.currentIndex()
        return False if index < 0 else self.close_tab_at(index)

    def open_tab_ids(self) -> List[str]:
        return [self._widget_ids.get(self.widget(index), "") for index in range(self.count()) if self.widget(index) is not None]

    def tab_entry_data(self) -> List[Tuple[str, str, str, bool]]:
        entries: List[Tuple[str, str, str, bool]] = []
        for tab_id in self.open_tab_ids():
            if not tab_id or tab_id in FIXED_SURFACE_TAB_IDS:
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
