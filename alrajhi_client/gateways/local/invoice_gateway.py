# -*- coding: utf-8 -*-
"""Local invoice gateway adapter.

This is the only gateway layer allowed to use the legacy invoice DAO.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from core.compat import pair
from database.dao.invoice_dao import invoice_dao
from gateways.invoice_gateway import InvoiceGateway


class LocalInvoiceGateway(InvoiceGateway):
    def list(self, search: str | None = None, inv_type: str | None = None,
             start_date: str | None = None, end_date: str | None = None,
             customer_id: int | None = None, supplier_id: int | None = None,
             limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]:
        return pair(invoice_dao.get_all(
            search=search, inv_type=inv_type, start_date=start_date, end_date=end_date,
            customer_id=customer_id, supplier_id=supplier_id, limit=limit, offset=offset
        ), 'invoices')

    def get(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        invoice = invoice_dao.get_by_id(invoice_id)
        return invoice if isinstance(invoice, dict) else None

    def create(self, data: Dict[str, Any]) -> int:
        return invoice_dao.create_invoice(data)

    def update(self, invoice_id: int, data: Dict[str, Any]):
        return invoice_dao.update_invoice(invoice_id, data)

    def delete(self, invoice_id: int):
        return invoice_dao.delete_invoice(invoice_id)

    def next_reference(self, inv_type: str) -> str:
        return invoice_dao.get_next_reference(inv_type)

    def has_linked_vouchers(self, invoice_id: int) -> bool:
        try:
            return bool(invoice_dao.repo.db._invoice_has_vouchers(invoice_id))
        except Exception:
            return False

    def is_remote(self) -> bool:
        return False
