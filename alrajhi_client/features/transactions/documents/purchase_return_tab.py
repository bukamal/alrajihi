from __future__ import annotations
from workspace.documents.document_contract import descriptor_for

from ..transaction_context import purchase_return_context
from ..transaction_document_tab import TransactionDocumentTab


class PurchaseReturnTab(TransactionDocumentTab):
    DOCUMENT_DESCRIPTOR = descriptor_for("purchase_return")
    def __init__(self, parent=None, return_id=None, return_data=None):
        # return_data is accepted for compatibility with legacy call sites;
        # the transaction tab loads by id through purchase_return_service.
        super().__init__(purchase_return_context(), parent=parent, invoice_id=return_id)
