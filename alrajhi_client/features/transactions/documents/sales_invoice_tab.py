from __future__ import annotations

from ..transaction_context import sales_invoice_context
from ..transaction_document_tab import TransactionDocumentTab


class SalesInvoiceTab(TransactionDocumentTab):
    def __init__(self, parent=None, invoice_id=None):
        super().__init__(sales_invoice_context(), parent=parent, invoice_id=invoice_id)
