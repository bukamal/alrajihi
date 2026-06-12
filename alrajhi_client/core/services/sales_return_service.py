# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from gateways.sales_return_gateway import SalesReturnException, create_sales_return_gateway


class SalesReturnService:
    """Application service for sales returns.

    Phase 12 keeps the public service API stable for widgets while moving all
    local/remote persistence and business execution behind SalesReturnGateway.
    """

    def __init__(self):
        self.gateway = create_sales_return_gateway()

    def next_return_no(self) -> str:
        return self.gateway.next_return_no()

    def list_returns(self, search: str | None = None, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict], int]:
        return self.gateway.list_returns(search=search, limit=limit, offset=offset)

    def get(self, return_id: int) -> Optional[Dict]:
        return self.gateway.get(return_id)

    def sale_invoices(self, search: str | None = None, limit: int = 200) -> List[Dict]:
        return self.gateway.sale_invoices(search=search, limit=limit)

    def returned_qty(self, invoice_id: int, line_id: int | None = None, item_id: int | None = None) -> Decimal:
        return self.gateway.returned_qty(invoice_id=invoice_id, line_id=line_id, item_id=item_id)

    def invoice_returnable_lines(self, invoice_id: int) -> List[Dict]:
        return self.gateway.invoice_returnable_lines(invoice_id)

    def create_return(self, data: Dict) -> int:
        return self.gateway.create_return(data)

    def delete_return(self, return_id: int) -> None:
        return self.gateway.delete_return(return_id)


sales_return_service = SalesReturnService()
