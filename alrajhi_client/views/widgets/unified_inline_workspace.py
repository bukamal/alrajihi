# -*- coding: utf-8 -*-
"""Unified inline master-detail workspace host.

Phase 380: every list workspace that embeds an editor should use the same
outer layout contract: compact master list, wide detail/editor pane, a minimal
back-only toolbar, shared dirty-close handling, and no duplicate title card in
the outer inline shell.
"""
from __future__ import annotations

from typing import Callable, Optional

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from i18n import translate
from workspace.documents.document_layout_policy import apply_document_layout_policy
from ui.components.responsive_master_detail import DetailPlaceholder, ResponsiveMasterDetail


def _back_text() -> str:
    value = translate('back')
    return 'عودة' if value == 'back' else value


class UnifiedInlineWorkspaceMixin:
    """Reusable inline editor shell for master-detail pages.

    It intentionally does not know how records are saved or loaded.  Concrete
    widgets pass editors into _show_unified_inline_editor(), then refresh their
    list when the editor emits saved.
    """

    def _install_unified_inline_workspace(
        self,
        master_widget,
        parent_layout,
        detail_title: str,
        *,
        close_callback: Optional[Callable[..., object]] = None,
        master_weight: int = 2,
        detail_weight: int = 3,
        total_width: int = 1420,
    ):
        self.detail_panel = DetailPlaceholder(detail_title)
        self.detail_stack = QStackedWidget(self)
        self.detail_stack.addWidget(self.detail_panel)

        self.inline_editor_page = QWidget(self)
        self.inline_editor_page.setObjectName('UnifiedInlineEditorPage')
        inline_layout = QVBoxLayout(self.inline_editor_page)
        inline_layout.setContentsMargins(0, 0, 0, 0)
        inline_layout.setSpacing(6)

        inline_toolbar = QHBoxLayout()
        inline_toolbar.setContentsMargins(0, 0, 0, 0)
        inline_toolbar.setSpacing(6)
        inline_toolbar.addStretch(1)
        self.inline_back_btn = QPushButton(_back_text(), self.inline_editor_page)
        self.inline_back_btn.setObjectName('UnifiedInlineBackButton')
        self.inline_back_btn.clicked.connect(close_callback or self._close_unified_inline_editor)
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

        self.master_detail = ResponsiveMasterDetail(
            master_widget,
            self.detail_stack,
            self,
            master_weight=master_weight,
            detail_weight=detail_weight,
        )
        try:
            QTimer.singleShot(0, lambda: self.master_detail.set_initial_sizes(total_width))
        except Exception:
            pass
        parent_layout.addWidget(self.master_detail, 1)
        return self.master_detail

    def _clear_unified_inline_editor(self):
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

    def _close_unified_inline_editor(self, *args, force: bool = False, preview_callback: Optional[Callable[..., object]] = None):
        editor = getattr(self, '_inline_editor', None)
        if editor is not None and not force and hasattr(editor, 'can_close'):
            if not editor.can_close():
                return False
        self._clear_unified_inline_editor()
        try:
            self.detail_stack.setCurrentWidget(self.detail_panel)
        except Exception:
            pass
        callback = preview_callback
        if callback is None:
            callback = getattr(self, '_update_detail_preview', None) or getattr(self, '_update_inline_detail_preview', None)
        if callable(callback):
            try:
                callback()
            except Exception:
                pass
        return True

    def _wire_unified_inline_close(self, editor, close_callback: Optional[Callable[..., object]] = None):
        callback = close_callback or self._close_unified_inline_editor
        for attr in ('bottom_close_btn', 'close_btn', 'cancel_btn'):
            btn = getattr(editor, attr, None)
            if btn is None or not hasattr(btn, 'clicked'):
                continue
            try:
                btn.clicked.disconnect()
            except Exception:
                pass
            try:
                btn.clicked.connect(lambda *_: callback())
            except Exception:
                pass

    def _apply_unified_inline_visual_policy(self, editor):
        try:
            editor.setProperty('inlineEditor', True)
        except Exception:
            pass
        # Phase381: delegate all embedded editor visuals to the canonical
        # document layout policy. It hides duplicate header cards, narrows
        # chrome, and applies the correct card/financial/tabular family.
        try:
            if hasattr(editor, 'apply_document_layout_profile'):
                editor.apply_document_layout_profile(inline=True)
            else:
                apply_document_layout_policy(editor, inline=True)
        except Exception:
            pass
        # Backward-compatible fallback for non-document editors.
        for attr in ('title_label', 'subtitle_label'):
            widget = getattr(editor, attr, None)
            if widget is not None and hasattr(widget, 'setVisible'):
                try:
                    widget.setVisible(False)
                except Exception:
                    pass

    def _show_unified_inline_editor(
        self,
        editor,
        *,
        saved_callback: Optional[Callable[..., object]] = None,
        close_callback: Optional[Callable[..., object]] = None,
    ):
        if getattr(self, '_inline_editor', None) is not None:
            closer = close_callback or self._close_unified_inline_editor
            if not closer():
                return None
        self._apply_unified_inline_visual_policy(editor)
        if saved_callback is not None:
            try:
                editor.saved.connect(saved_callback)
            except Exception:
                pass
        self._wire_unified_inline_close(editor, close_callback)
        self.inline_editor_host_layout.addWidget(editor)
        self._inline_editor = editor
        self.detail_stack.setCurrentWidget(self.inline_editor_page)
        return editor
