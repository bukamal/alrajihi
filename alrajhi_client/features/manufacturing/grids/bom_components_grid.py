# -*- coding: utf-8 -*-
from __future__ import annotations

from features.transactions.grids.transaction_line_grid import TransactionLineGrid


class BomComponentsGrid(TransactionLineGrid):
    """Professional BOM components grid sharing transaction table behaviour."""

    def __init__(self, columns=None, parent=None, identity: str = 'manufacturing.bom.components'):
        super().__init__(columns=columns, parent=parent, identity=identity)
        self.configure_item_delegate(
            items_provider=self._component_items,
            price_key_provider=lambda: 'purchase_price',
        )

    def _component_items(self, search: str | None = None, limit: int = 60):
        try:
            from core.services.catalog_service import catalog_service
            rows = catalog_service.items(search=search or None, limit=limit) or []
            return [row for row in rows if row.get('item_type') in ('مخزون', 'منتج نهائي', 'raw_material', 'finished_product', 'stock')]
        except Exception:
            return []
