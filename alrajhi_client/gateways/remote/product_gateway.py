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
        """Return a material by exact barcode without downloading the catalog.

        Barcode scanner flows must be deterministic: no loose search and no
        first-row fallback.  The preferred API endpoint is /api/items/by-barcode.
        The bounded fallback below exists only for old servers and still keeps
        exact-match semantics.
        """
        value = str(barcode or '').strip()
        if not value:
            return None
        try:
            item = self.rest_client.get_item_by_barcode(value)
            return item if isinstance(item, dict) else None
        except Exception:
            # Backward compatibility with older servers: use a bounded server-side
            # text search and accept only an exact barcode match.  Never call
            # self.list() without filters here.
            items, _ = self.list(search=value, limit=10, offset=0)
            exact = [item for item in (items or []) if str(item.get('barcode') or '').strip() == value]
            return exact[0] if len(exact) == 1 else None

    def create(self, data: Dict[str, Any]) -> int:
        return self.rest_client.add_item(data)

    def update(self, item_id: int, data: Dict[str, Any]):
        return self.rest_client.update_item(item_id, data)

    def delete(self, item_id: int):
        return self.rest_client.delete_item(item_id)

    def get_units(self, item_id: int) -> List[Dict]:
        item = self.get(item_id) or {}
        return item.get('units', []) or []

    def add_unit(self, item_id: int, unit_name: str, conversion_factor: float, barcode: str | None = None, notes: str = ''):
        raise NotImplementedError("Remote item units are saved atomically through item create/update payloads.")

    def clear_units(self, item_id: int):
        raise NotImplementedError("Remote item units are saved atomically through item create/update payloads.")

    def get_variants(self, item_id: int) -> List[Dict]:
        return self.rest_client.get_item_variants(item_id)

    def get_variant_by_barcode(self, barcode: str) -> Optional[Dict]:
        variant = self.rest_client.get_item_variant_by_barcode(barcode)
        return variant if isinstance(variant, dict) else None

    def add_variant(self, item_id: int, data: Dict[str, Any]) -> int:
        return self.rest_client.add_item_variant(item_id, data)

    def update_variant(self, variant_id: int, data: Dict[str, Any]):
        return self.rest_client.update_item_variant(variant_id, data)

    def delete_variant(self, variant_id: int):
        return self.rest_client.delete_item_variant(variant_id)

    def apparel_report(self, item_id: int | None = None) -> Dict[str, Any]:
        return self.rest_client.get_apparel_report(item_id=item_id)

    def sold_quantities(self, item_ids: list[int]) -> Dict[int, Decimal]:
        ids = [int(x) for x in (item_ids or []) if x is not None]
        if not ids:
            return {}
        try:
            values = self.rest_client.get_item_sold_quantities(ids)
            return {i: Decimal(str(values.get(i, 0))) for i in ids}
        except Exception:
            return {i: Decimal('0') for i in ids}


    def activity_summary(self, item_id: int) -> Dict[str, Any]:
        try:
            return self.rest_client.get_item_activity_summary(int(item_id or 0)) or {}
        except Exception:
            return {'blocking_total': 0, 'has_movements': False}

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


    def activity_summary(self, item_id: int) -> Dict[str, Any]:
        try:
            return self.rest_client.get_item_activity_summary(int(item_id or 0)) or {}
        except Exception:
            return {'blocking_total': 0, 'has_movements': False}

    def is_remote(self) -> bool:
        return True
