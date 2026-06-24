# -*- coding: utf-8 -*-
"""Unified inline editor host for party list workspaces.

Phase 380: customers and suppliers now use the same generic inline workspace
shell as users/categories/warehouses/branches/cashboxes/vouchers while keeping
party-specific editor construction isolated here.
"""
from __future__ import annotations

from typing import Optional

from utils import show_toast
from views.widgets.unified_inline_workspace import UnifiedInlineWorkspaceMixin


class PartyInlineEditorHostMixin(UnifiedInlineWorkspaceMixin):
    """Shared inline editor behavior for customer/supplier list screens."""

    def _install_party_inline_host(self, table, parent_layout, detail_title: str):
        return self._install_unified_inline_workspace(
            table,
            parent_layout,
            detail_title,
            close_callback=self._close_inline_party_editor,
            master_weight=2,
            detail_weight=3,
            total_width=1420,
        )

    def _clear_inline_party_editor(self):
        return self._clear_unified_inline_editor()

    def _close_inline_party_editor(self, *args, force: bool = False):
        return self._close_unified_inline_editor(
            *args,
            force=force,
            preview_callback=getattr(self, '_update_detail_preview', None),
        )

    def _after_inline_party_saved(self, saved_id=None):
        try:
            self.refresh()
        finally:
            self._close_inline_party_editor(force=True)

    def _wire_inline_party_close(self, editor):
        return self._wire_unified_inline_close(editor, self._close_inline_party_editor)

    def _show_inline_party_editor(self, party_type: str, party_id: Optional[object] = None):
        if getattr(self, '_inline_editor', None) is not None:
            if not self._close_inline_party_editor():
                return None
        try:
            from features.parties import PartyEditorTab
            editor = PartyEditorTab(self.inline_editor_host, party_type=party_type, party_id=party_id, inline_mode=True)
            return self._show_unified_inline_editor(
                editor,
                saved_callback=self._after_inline_party_saved,
                close_callback=self._close_inline_party_editor,
            )
        except Exception as exc:
            show_toast(str(exc), 'error', self)
            return None
