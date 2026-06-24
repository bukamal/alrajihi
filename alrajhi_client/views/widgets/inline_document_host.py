# -*- coding: utf-8 -*-
"""Reusable inline master-detail document host for list workspaces.

Phase 377: list-management workspaces such as users, categories, warehouses,
and branches must behave like customers/suppliers/vouchers: Add/Edit opens an
embedded editor in the detail pane, not a new workspace tab.
"""
from __future__ import annotations

from typing import Callable, Optional

from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from i18n import translate
from ui.components.responsive_master_detail import DetailPlaceholder, ResponsiveMasterDetail


class InlineDocumentHostMixin:
    """Mixin that embeds BaseDocumentTab-like editors in a detail pane."""

    def _install_inline_document_host(self, table, parent_layout, detail_title: str):
        self.detail_panel = DetailPlaceholder(detail_title)
        self.detail_stack = QStackedWidget(self)
        self.detail_stack.addWidget(self.detail_panel)

        self.inline_editor_page = QWidget(self)
        inline_layout = QVBoxLayout(self.inline_editor_page)
        inline_layout.setContentsMargins(0, 0, 0, 0)
        inline_layout.setSpacing(8)

        inline_header = QHBoxLayout()
        self.inline_title_label = QLabel('', self.inline_editor_page)
        self.inline_title_label.setObjectName('InlineEditorTitle')
        self.inline_back_btn = QPushButton(translate('back') if translate('back') != 'back' else 'عودة', self.inline_editor_page)
        self.inline_back_btn.clicked.connect(self._close_inline_document)
        inline_header.addWidget(self.inline_title_label, 1)
        inline_header.addWidget(self.inline_back_btn)
        inline_layout.addLayout(inline_header)

        self.inline_editor_host = QWidget(self.inline_editor_page)
        self.inline_editor_host_layout = QVBoxLayout(self.inline_editor_host)
        self.inline_editor_host_layout.setContentsMargins(0, 0, 0, 0)
        self.inline_editor_host_layout.setSpacing(0)
        inline_layout.addWidget(self.inline_editor_host, 1)
        self._inline_editor = None
        self.detail_stack.addWidget(self.inline_editor_page)

        self.master_detail = ResponsiveMasterDetail(table, self.detail_stack, self)
        parent_layout.addWidget(self.master_detail, 1)
        return self.master_detail

    def _clear_inline_document(self):
        editor = getattr(self, '_inline_editor', None)
        if editor is None:
            return
        try:
            self.inline_editor_host_layout.removeWidget(editor)
        except Exception:
            pass
        try:
            editor.setParent(None)
            editor.deleteLater()
        except Exception:
            pass
        self._inline_editor = None

    def _close_inline_document(self, *args, force: bool = False):
        editor = getattr(self, '_inline_editor', None)
        if editor is not None and not force and hasattr(editor, 'can_close'):
            if not editor.can_close():
                return False
        self._clear_inline_document()
        try:
            self.detail_stack.setCurrentWidget(self.detail_panel)
        except Exception:
            pass
        try:
            self._update_inline_detail_preview()
        except Exception:
            pass
        return True

    def _after_inline_document_saved(self, saved_id=None):
        try:
            self.refresh()
        finally:
            self._close_inline_document(force=True)

    def _wire_inline_editor_close(self, editor):
        # Embedded editors must close only the inline detail panel, not the full
        # workspace tab.  Many document tabs expose bottom_close_btn/close_btn.
        for attr in ('bottom_close_btn', 'close_btn', 'cancel_btn'):
            btn = getattr(editor, attr, None)
            if btn is None or not hasattr(btn, 'clicked'):
                continue
            try:
                btn.clicked.disconnect()
            except Exception:
                pass
            try:
                btn.clicked.connect(lambda *_: self._close_inline_document())
            except Exception:
                pass

    def _show_inline_document(self, editor, title: Optional[str] = None):
        if getattr(self, '_inline_editor', None) is not None:
            if not self._close_inline_document():
                return None
        try:
            editor.setProperty('inlineEditor', True)
        except Exception:
            pass
        if title:
            try:
                self.inline_title_label.setText(title)
            except Exception:
                pass
        try:
            if hasattr(editor, 'workspace_title'):
                self.inline_title_label.setText(editor.workspace_title())
            elif editor.windowTitle():
                self.inline_title_label.setText(editor.windowTitle())
        except Exception:
            pass
        try:
            editor.titleChanged.connect(lambda txt: self.inline_title_label.setText(txt))
        except Exception:
            pass
        try:
            editor.saved.connect(self._after_inline_document_saved)
        except Exception:
            pass
        self._wire_inline_editor_close(editor)
        self.inline_editor_host_layout.addWidget(editor)
        self._inline_editor = editor
        self.detail_stack.setCurrentWidget(self.inline_editor_page)
        return editor

    def _selected_inline_row_data(self):
        table = getattr(self, 'table', None)
        model = getattr(self, 'model', None)
        if table is None or model is None:
            return {}
        sm = table.selectionModel() if hasattr(table, 'selectionModel') else None
        if sm is None or not sm.selectedRows():
            return {}
        try:
            row = table.current_source_row() if hasattr(table, 'current_source_row') else sm.selectedRows()[0].row()
            return model.get_row(row) if hasattr(model, 'get_row') else {}
        except Exception:
            return {}

    def _connect_inline_detail_preview(self):
        table = getattr(self, 'table', None)
        sm = table.selectionModel() if table is not None and hasattr(table, 'selectionModel') else None
        if sm is None:
            return
        try:
            sm.selectionChanged.disconnect(self._update_inline_detail_preview)
        except Exception:
            pass
        sm.selectionChanged.connect(self._update_inline_detail_preview)
        self._update_inline_detail_preview()

    def _update_inline_detail_preview(self, *args):
        panel = getattr(self, 'detail_panel', None)
        if panel is None:
            return
        data = self._selected_inline_row_data()
        if not data:
            panel.clear_summary()
            return
        title = data.get('name') or data.get('username') or data.get('full_name') or data.get('code') or data.get('status') or ''
        lines = []
        for key, value in data.items():
            if key in ('id', '_row_status') or value in (None, ''):
                continue
            if len(lines) >= 5:
                break
            label = translate(key)
            if label == key:
                label = key.replace('_', ' ')
            lines.append(f"{label}: {value}")
        lines.append(translate('double_click_to_open_document') if translate('double_click_to_open_document') != 'double_click_to_open_document' else 'انقر مرتين للتحرير داخل نفس التبويب')
        panel.set_summary(str(title), lines)
