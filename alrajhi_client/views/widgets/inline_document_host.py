# -*- coding: utf-8 -*-
"""Reusable inline master-detail document host for list workspaces.

Phase 380 delegates the outer shell to UnifiedInlineWorkspaceMixin so all
management editors share one inline layout: compact list, wide editor pane,
minimal back-only toolbar, and no duplicate outer title label.
"""
from __future__ import annotations

from typing import Optional

from i18n import translate
from views.widgets.unified_inline_workspace import UnifiedInlineWorkspaceMixin


class InlineDocumentHostMixin(UnifiedInlineWorkspaceMixin):
    """Mixin that embeds BaseDocumentTab-like editors in a unified detail pane."""

    def _install_inline_document_host(self, table, parent_layout, detail_title: str):
        return self._install_unified_inline_workspace(
            table,
            parent_layout,
            detail_title,
            close_callback=self._close_inline_document,
            master_weight=2,
            detail_weight=3,
            total_width=1420,
        )

    def _clear_inline_document(self):
        return self._clear_unified_inline_editor()

    def _close_inline_document(self, *args, force: bool = False):
        return self._close_unified_inline_editor(
            *args,
            force=force,
            preview_callback=getattr(self, '_update_inline_detail_preview', None),
        )

    def _after_inline_document_saved(self, saved_id=None):
        try:
            self.refresh()
        finally:
            self._close_inline_document(force=True)

    def _wire_inline_editor_close(self, editor):
        return self._wire_unified_inline_close(editor, self._close_inline_document)

    def _show_inline_document(self, editor, title: Optional[str] = None):
        # `title` is kept as a compatibility parameter for older callers; the
        # unified inline shell intentionally does not render a duplicate title.
        return self._show_unified_inline_editor(
            editor,
            saved_callback=self._after_inline_document_saved,
            close_callback=self._close_inline_document,
        )

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
