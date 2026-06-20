# -*- coding: utf-8 -*-
"""Remote API sales-return gateway adapter."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from gateways.sales_return_gateway import SalesReturnGateway


class RemoteSalesReturnGateway(SalesReturnGateway):
    def __init__(self, rest_client):
        self.rest_client = rest_client

    def next_return_no(self) -> str:
        # The server generates the final number during create_return.
        return f"SR-{datetime.now().strftime('%Y')}-AUTO"

    def list_returns(self, search: str | None = None, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]:
        return self.rest_client.get_sales_returns(search=search, limit=limit, offset=offset)

    def get(self, return_id: int) -> Optional[Dict[str, Any]]:
        result = self.rest_client.get_sales_return(return_id)
        return result if isinstance(result, dict) else None

    def sale_invoices(self, search: str | None = None, limit: int = 200) -> List[Dict[str, Any]]:
        return self.rest_client.get_sales_return_invoices(search=search, limit=limit)

    def returned_qty(self, invoice_id: int, line_id: int | None = None, item_id: int | None = None) -> Decimal:
        # Remote returnable quantities are calculated by the server endpoint.
        return Decimal('0')

    def invoice_returnable_lines(self, invoice_id: int) -> List[Dict[str, Any]]:
        return self.rest_client.get_sales_returnable_lines(invoice_id)

    def create_return(self, data: Dict[str, Any]) -> int:
        result = self.rest_client.create_sales_return(data)
        return int((result or {}).get('id') or 0)

    def delete_return(self, return_id: int) -> None:
        self.rest_client.delete_sales_return(return_id)

    def update_return(self, return_id: int, data: Dict[str, Any]) -> int:
        result = self.rest_client.update_sales_return(return_id, data)
        return int((result or {}).get('id') or return_id)

    def is_remote(self) -> bool:
        return True
