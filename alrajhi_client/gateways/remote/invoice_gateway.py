# -*- coding: utf-8 -*-
"""Remote API invoice gateway adapter."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from gateways.invoice_gateway import InvoiceGateway


class RemoteInvoiceGateway(InvoiceGateway):
    def __init__(self, rest_client):
        self.rest_client = rest_client

    def list(self, search: str | None = None, inv_type: str | None = None,
             start_date: str | None = None, end_date: str | None = None,
             customer_id: int | None = None, supplier_id: int | None = None,
             limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]:
        return self.rest_client.get_invoices(
            inv_type=inv_type, start_date=start_date, end_date=end_date,
            limit=limit, offset=offset, search=search,
            customer_id=customer_id, supplier_id=supplier_id
        )

    def get(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        invoice = self.rest_client.get_invoice_by_id(invoice_id)
        return invoice if isinstance(invoice, dict) else None

    def create(self, data: Dict[str, Any]) -> int:
        return self.rest_client.add_invoice(data)

    def update(self, invoice_id: int, data: Dict[str, Any]):
        return self.rest_client.update_invoice(invoice_id, data)

    def delete(self, invoice_id: int):
        return self.rest_client.delete_invoice(invoice_id)

    def next_reference(self, inv_type: str) -> str:
        return self.rest_client.get_next_invoice_reference(inv_type)

    def has_linked_vouchers(self, invoice_id: int) -> bool:
        # No dedicated remote endpoint exists yet.  Remote update/delete endpoints
        # enforce this rule server-side, so this method remains conservative for
        # pre-check UI flows without duplicating server SQL in the client.
        return False

    def has_linked_returns(self, invoice_id: int) -> bool:
        # Server update/delete endpoints enforce linked-return guards.
        return False

    def is_remote(self) -> bool:
        return True
