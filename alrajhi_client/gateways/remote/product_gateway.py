# -*- coding: utf-8 -*-
"""Remote API item/category gateway adapters."""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from gateways.product_gateway import ItemGateway, CategoryGateway


class RemoteItemGateway(ItemGateway):
    def __init__(self, rest_client):
        self.rest_client = rest_client

    def list(self, search: str | None = None, limit: int | None = None,
             offset: int | None = None) -> Tuple[List[Dict], int]:
        return self.rest_client.get_items(search=search, limit=limit, offset=offset)

    def get(self, item_id: int) -> Optional[Dict]:
        item = self.rest_client.get_item(item_id)
        return item if isinstance(item, dict) else None

    def get_by_barcode(self, barcode: str) -> Optional[Dict]:
        items, _ = self.list()
        for item in items:
            if str(item.get('barcode') or '') == str(barcode or ''):
                return item
        return None

    def create(self, data: Dict[str, Any]) -> int:
        return self.rest_client.add_item(data)

    def update(self, item_id: int, data: Dict[str, Any]):
        return self.rest_client.update_item(item_id, data)

    def delete(self, item_id: int):
        return self.rest_client.delete_item(item_id)

    def get_units(self, item_id: int) -> List[Dict]:
        item = self.get(item_id) or {}
        return item.get('units', []) or []

    def add_unit(self, item_id: int, unit_name: str, conversion_factor: float):
        raise NotImplementedError("Remote item units are saved atomically through item create/update payloads.")

    def clear_units(self, item_id: int):
        raise NotImplementedError("Remote item units are saved atomically through item create/update payloads.")

    def sold_quantities(self, item_ids: list[int]) -> Dict[int, Decimal]:
        # No remote aggregate endpoint exists yet. Preserve the previous remote
        # behavior by returning zero quantities until the API adds this read model.
        ids = [int(x) for x in (item_ids or []) if x is not None]
        return {i: Decimal('0') for i in ids}

    def is_remote(self) -> bool:
        return True


class RemoteCategoryGateway(CategoryGateway):
    def __init__(self, rest_client):
        self.rest_client = rest_client

    def list(self, search: str | None = None, include_inactive: bool = False,
             include_deleted: bool = False) -> List[Dict]:
        return self.rest_client.get_categories(search=search, include_inactive=include_inactive, include_deleted=include_deleted)

    def get(self, category_id: int) -> Optional[Dict]:
        for category in self.list(include_inactive=True, include_deleted=True):
            if int(category.get('id', 0)) == int(category_id):
                return category
        return None

    def create(self, data: Dict[str, Any]) -> int:
        return self.rest_client.add_category(data)

    def update(self, category_id: int, data: Dict[str, Any]):
        return self.rest_client.update_category(category_id, data)

    def delete(self, category_id: int):
        return self.rest_client.delete_category(category_id)

    def restore(self, category_id: int):
        return self.rest_client.restore_category(category_id)
