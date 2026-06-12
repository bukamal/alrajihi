# -*- coding: utf-8 -*-
"""Catalog lookup service for UI dialogs.

The project historically returned collections as list, (list, total), or dict
payloads depending on local/REST/DAO path.  Dialogs need clean records, while
paginated widgets need pairs.  This module centralizes catalog normalization so
UI files do not contain repeated tuple/list defensive code.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from core.compat import records
from core.services.product_service import product_service
from core.services.entity_service import entity_service


class CatalogService:
    """Read-only catalog facade over legacy DAO objects."""

    def items(self, search: str | None = None, limit: int | None = None, offset: int | None = None) -> List[Dict]:
        return product_service.items(search=search, limit=limit, offset=offset)

    def items_pair(self, search: str | None = None, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict], int]:
        return product_service.items_pair(search=search, limit=limit, offset=offset)

    def customers(self, search: str | None = None, limit: int | None = None, offset: int | None = None) -> List[Dict]:
        return records(entity_service.customers(search=search, limit=limit, offset=offset), 'customers')

    def customers_pair(self, search: str | None = None, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict], int]:
        return entity_service.customers(search=search, limit=limit, offset=offset)

    def suppliers(self, search: str | None = None, limit: int | None = None, offset: int | None = None) -> List[Dict]:
        return records(entity_service.suppliers(search=search, limit=limit, offset=offset), 'suppliers')

    def suppliers_pair(self, search: str | None = None, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict], int]:
        return entity_service.suppliers(search=search, limit=limit, offset=offset)

    def item_units(self, item_id: int) -> List[Dict]:
        return product_service.item_units(item_id)

    def item_by_id(self, item_id: int) -> Optional[Dict]:
        return product_service.item_by_id(item_id)

    def customer_by_id(self, customer_id: int) -> Optional[Dict]:
        return entity_service.customer_by_id(customer_id)

    def supplier_by_id(self, supplier_id: int) -> Optional[Dict]:
        return entity_service.supplier_by_id(supplier_id)


catalog_service = CatalogService()
