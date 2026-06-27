# -*- coding: utf-8 -*-
"""Item/category gateway contracts and factory.

The UI and application services should use these contracts instead of importing
item/category DAO classes directly.  Local DAO access is confined to the local
adapter; remote mode is confined to the remote adapter.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple


class ItemGateway(ABC):
    @abstractmethod
    def list(self, search: str | None = None, limit: int | None = None,
             offset: int | None = None) -> Tuple[List[Dict], int]:
        raise NotImplementedError

    @abstractmethod
    def get(self, item_id: int) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def get_by_barcode(self, barcode: str) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> int:
        raise NotImplementedError

    @abstractmethod
    def update(self, item_id: int, data: Dict[str, Any]):
        raise NotImplementedError

    @abstractmethod
    def delete(self, item_id: int):
        raise NotImplementedError

    @abstractmethod
    def get_units(self, item_id: int) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def add_unit(self, item_id: int, unit_name: str, conversion_factor: float, barcode: str | None = None, notes: str = ''):
        raise NotImplementedError

    @abstractmethod
    def clear_units(self, item_id: int):
        raise NotImplementedError

    @abstractmethod
    def get_variants(self, item_id: int) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def get_variant_by_barcode(self, barcode: str) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def add_variant(self, item_id: int, data: Dict[str, Any]) -> int:
        raise NotImplementedError

    @abstractmethod
    def update_variant(self, variant_id: int, data: Dict[str, Any]):
        raise NotImplementedError

    @abstractmethod
    def delete_variant(self, variant_id: int):
        raise NotImplementedError

    @abstractmethod
    def apparel_report(self, item_id: int | None = None) -> Dict[str, Any]:
        """Return apparel variant stock, sales, and low-stock report rows.

        Implementations must preserve the gateway boundary for local/API mode.
        """
        raise NotImplementedError

    @abstractmethod
    def sold_quantities(self, item_ids: list[int]) -> Dict[int, Decimal]:
        """Return net sold quantities per item in base unit.

        Net sold = sale invoice quantities - non-cancelled sales returns.
        Implementations must hide local SQL/API details from ProductService.
        """
        raise NotImplementedError

    @abstractmethod
    def activity_summary(self, item_id: int) -> Dict[str, Any]:
        """Return material usage counts used by security/settings policy.

        UI code must not query invoice_lines, inventory_movements, BOM or
        production tables directly.  Local/remote adapters are responsible for
        translating this request to SQL or REST.
        """
        raise NotImplementedError

    @abstractmethod
    def bom_usage(self, item_id: int) -> Dict[str, Any]:
        """Return concrete BOM recipes/products that reference this material.

        This is the Phase391 resolver used to explain item-delete blockers without
        leaking raw SQL table names such as bom_line.
        """
        raise NotImplementedError

    @abstractmethod
    def is_remote(self) -> bool:
        raise NotImplementedError


class CategoryGateway(ABC):
    @abstractmethod
    def list(self, search: str | None = None, include_inactive: bool = False,
             include_deleted: bool = False) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def get(self, category_id: int) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> int:
        raise NotImplementedError

    @abstractmethod
    def update(self, category_id: int, data: Dict[str, Any]):
        raise NotImplementedError

    @abstractmethod
    def delete(self, category_id: int):
        raise NotImplementedError

    @abstractmethod
    def restore(self, category_id: int):
        raise NotImplementedError


def create_product_gateways():
    """Return the active item/category gateways."""
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.product_gateway import RemoteItemGateway, RemoteCategoryGateway
        rest_client = db.get_rest_client()
        return RemoteItemGateway(rest_client), RemoteCategoryGateway(rest_client)

    from gateways.local.product_gateway import LocalItemGateway, LocalCategoryGateway
    return LocalItemGateway(), LocalCategoryGateway()
