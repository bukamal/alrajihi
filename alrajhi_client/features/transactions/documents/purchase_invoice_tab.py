from __future__ import annotations
from workspace.documents.document_contract import descriptor_for

from ..transaction_context import purchase_invoice_context
from ..transaction_document_tab import TransactionDocumentTab


class PurchaseInvoiceTab(TransactionDocumentTab):
    DOCUMENT_DESCRIPTOR = descriptor_for("purchase_invoice")
    def __init__(self, parent=None, invoice_id=None):
        super().__init__(purchase_invoice_context(), parent=parent, invoice_id=invoice_id)
