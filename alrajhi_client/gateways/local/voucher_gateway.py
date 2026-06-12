# -*- coding: utf-8 -*-
"""Local voucher gateway adapter.

This is the only gateway layer allowed to use the legacy voucher DAO.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from core.compat import pair
from database.dao.voucher_dao import voucher_dao
from gateways.voucher_gateway import VoucherGateway


class LocalVoucherGateway(VoucherGateway):
    def list(self, search: str | None = None, vtype: str | None = None,
             limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]:
        return pair(voucher_dao.get_all(search=search, vtype=vtype, limit=limit, offset=offset), 'vouchers')

    def get(self, voucher_id: int) -> Optional[Dict[str, Any]]:
        voucher = voucher_dao.get_by_id(voucher_id)
        return voucher if isinstance(voucher, dict) else None

    def create(self, data: Dict[str, Any]) -> int:
        return voucher_dao.add(data)

    def update(self, voucher_id: int, data: Dict[str, Any]):
        return voucher_dao.update(voucher_id, data)

    def delete(self, voucher_id: int):
        return voucher_dao.delete(voucher_id)

    def is_remote(self) -> bool:
        return False
