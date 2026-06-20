# -*- coding: utf-8 -*-
from __future__ import annotations

from views.dialogs.invoice_dialog import InvoiceDialog
from i18n import translate
from workspace.documents.document_contract import descriptor_for


class InvoiceEditorTab(InvoiceDialog):
    LEGACY_TRANSACTION_ADAPTER = True
    DOCUMENT_DESCRIPTOR_BY_INVOICE_TYPE = {'sale': descriptor_for('sales_invoice'), 'purchase': descriptor_for('purchase_invoice')}
    """Legacy invoice document adapter.

    TransactionDocumentTab is the official shell. This adapter is retained only
    for emergency rollback when features/allow_legacy_transaction_documents is enabled.

    InvoiceDialog already exposes workspace_save/print/export and dirtyChanged;
    this subclass gives the workspace a stable feature-level entry point while
    the long dialog is decomposed into Header/Lines/Totals/Payments components.
    """

    def __init__(self, parent=None, inv_type='sale', invoice_id=None) -> None:
        super().__init__(inv_type, parent=parent, invoice_id=invoice_id, embedded=True)
        self.document_type = f'{inv_type}_invoice'
        self.document_id = invoice_id
        self.document_descriptor = self.DOCUMENT_DESCRIPTOR_BY_INVOICE_TYPE.get(inv_type)
        self.setWindowTitle(self.workspace_title())

    def can_close(self) -> bool:
        if hasattr(self, '_confirm_discard_changes'):
            return self._confirm_discard_changes()
        return True
