# -*- coding: utf-8 -*-
from __future__ import annotations

from views.dialogs.invoice_dialog import InvoiceDialog
from i18n import translate


class InvoiceEditorTab(InvoiceDialog):
    """Invoice document tab.

    InvoiceDialog already exposes workspace_save/print/export and dirtyChanged;
    this subclass gives the workspace a stable feature-level entry point while
    the long dialog is decomposed into Header/Lines/Totals/Payments components.
    """

    def __init__(self, parent=None, inv_type='sale', invoice_id=None) -> None:
        super().__init__(inv_type, parent=parent, invoice_id=invoice_id, embedded=True)
        self.document_type = f'{inv_type}_invoice'
        self.document_id = invoice_id
        self.setWindowTitle(self.workspace_title())

    def can_close(self) -> bool:
        if hasattr(self, '_confirm_discard_changes'):
            return self._confirm_discard_changes()
        return True
