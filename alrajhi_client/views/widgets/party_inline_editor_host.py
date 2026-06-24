# -*- coding: utf-8 -*-
"""Unified inline editor host for party list workspaces.

Phase 379: customers and suppliers use the same embedded editor surface:
wide detail pane, compact back-only toolbar, and no duplicate document title card.
"""
from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from i18n import translate
from ui.components.responsive_master_detail import DetailPlaceholder, ResponsiveMasterDetail
from utils import show_toast


class PartyInlineEditorHostMixin:
    """Shared inline editor behavior for customer/supplier list screens."""

    def _install_party_inline_host(self, table, parent_layout, detail_title: str):
        self.detail_panel = DetailPlaceholder(detail_title)
        self.detail_stack = QStackedWidget(self)
        self.detail_stack.addWidget(self.detail_panel)

        self.inline_editor_page = QWidget(self)
        self.inline_editor_page.setObjectName('UnifiedInlineEditorPage')
        inline_layout = QVBoxLayout(self.inline_editor_page)
        inline_layout.setContentsMargins(0, 0, 0, 0)
        inline_layout.setSpacing(6)

        # Unified inline structure: keep only navigation/actions in the outer
        # host.  The embedded document supplies its own functional fields, and
        # PartyEditorTab hides its document title card when inline_mode=True.
        inline_toolbar = QHBoxLayout()
        inline_toolbar.setContentsMargins(0, 0, 0, 0)
        inline_toolbar.setSpacing(6)
        inline_toolbar.addStretch(1)
        self.inline_back_btn = QPushButton(translate('back') if translate('back') != 'back' else 'عودة', self.inline_editor_page)
        self.inline_back_btn.setObjectName('InlineEditorBackButton')
        self.inline_back_btn.clicked.connect(self._close_inline_party_editor)
        inline_toolbar.addWidget(self.inline_back_btn)
        inline_layout.addLayout(inline_toolbar)

        self.inline_editor_host = QWidget(self.inline_editor_page)
        self.inline_editor_host.setObjectName('UnifiedInlineEditorHost')
        self.inline_editor_host_layout = QVBoxLayout(self.inline_editor_host)
        self.inline_editor_host_layout.setContentsMargins(0, 0, 0, 0)
        self.inline_editor_host_layout.setSpacing(0)
        inline_layout.addWidget(self.inline_editor_host, 1)
        self._inline_editor = None
        self.detail_stack.addWidget(self.inline_editor_page)

        self.master_detail = ResponsiveMasterDetail(table, self.detail_stack, self, master_weight=2, detail_weight=3)
        try:
            QTimer.singleShot(0, lambda: self.master_detail.set_initial_sizes(1420))
        except Exception:
            pass
        parent_layout.addWidget(self.master_detail, 1)
        return self.master_detail

    def _clear_inline_party_editor(self):
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

    def _close_inline_party_editor(self, *args, force: bool = False):
        editor = getattr(self, '_inline_editor', None)
        if editor is not None and not force and hasattr(editor, 'can_close'):
            if not editor.can_close():
                return False
        self._clear_inline_party_editor()
        try:
            self.detail_stack.setCurrentWidget(self.detail_panel)
        except Exception:
            pass
        try:
            self._update_detail_preview()
        except Exception:
            pass
        return True

    def _after_inline_party_saved(self, saved_id=None):
        try:
            self.refresh()
        finally:
            self._close_inline_party_editor(force=True)

    def _wire_inline_party_close(self, editor):
        for attr in ('bottom_close_btn', 'close_btn', 'cancel_btn'):
            btn = getattr(editor, attr, None)
            if btn is None or not hasattr(btn, 'clicked'):
                continue
            try:
                btn.clicked.disconnect()
            except Exception:
                pass
            try:
                btn.clicked.connect(lambda *_: self._close_inline_party_editor())
            except Exception:
                pass

    def _show_inline_party_editor(self, party_type: str, party_id: Optional[object] = None):
        if getattr(self, '_inline_editor', None) is not None:
            if not self._close_inline_party_editor():
                return None
        try:
            from features.parties import PartyEditorTab
            editor = PartyEditorTab(self.inline_editor_host, party_type=party_type, party_id=party_id, inline_mode=True)
            editor.setProperty('inlineEditor', True)
            editor.saved.connect(self._after_inline_party_saved)
            self._wire_inline_party_close(editor)
            self.inline_editor_host_layout.addWidget(editor)
            self._inline_editor = editor
            self.detail_stack.setCurrentWidget(self.inline_editor_page)
            return editor
        except Exception as exc:
            show_toast(str(exc), 'error', self)
            return None
