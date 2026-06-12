# -*- coding: utf-8 -*-
"""Remote API voucher gateway adapter."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from gateways.voucher_gateway import VoucherGateway


class RemoteVoucherGateway(VoucherGateway):
    def __init__(self, rest_client):
        self.rest_client = rest_client

    def list(self, search: str | None = None, vtype: str | None = None,
             limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]:
        # The current remote voucher endpoint supports type/pagination.  The
        # search argument remains in the contract for service compatibility and
        # future endpoint expansion without another service refactor.
        return self.rest_client.get_vouchers(vtype=vtype, limit=limit, offset=offset)

    def get(self, voucher_id: int) -> Optional[Dict[str, Any]]:
        voucher = self.rest_client.get_voucher(voucher_id)
        return voucher if isinstance(voucher, dict) else None

    def create(self, data: Dict[str, Any]) -> int:
        return self.rest_client.add_voucher(data)

    def update(self, voucher_id: int, data: Dict[str, Any]):
        return self.rest_client.update_voucher(voucher_id, data)

    def delete(self, voucher_id: int):
        return self.rest_client.delete_voucher(voucher_id)

    def is_remote(self) -> bool:
        return True
