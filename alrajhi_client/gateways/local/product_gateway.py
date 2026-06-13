# -*- coding: utf-8 -*-
"""Local item/category gateway adapters.

This is the only gateway layer allowed to use the legacy item/category DAO.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from core.compat import records, pair
from gateways.product_gateway import ItemGateway, CategoryGateway
from database.dao.item_dao import item_dao
from database.dao.category_dao import category_dao


class LocalItemGateway(ItemGateway):
    def list(self, search: str | None = None, limit: int | None = None,
             offset: int | None = None) -> Tuple[List[Dict], int]:
        return pair(item_dao.get_items(search=search, limit=limit, offset=offset), 'items')

    def get(self, item_id: int) -> Optional[Dict]:
        item = item_dao.get_by_id(item_id)
        return item if isinstance(item, dict) else None

    def get_by_barcode(self, barcode: str) -> Optional[Dict]:
        item = item_dao.get_by_barcode(barcode)
        return item if isinstance(item, dict) else None

    def create(self, data: Dict[str, Any]) -> int:
        return item_dao.add(data)

    def update(self, item_id: int, data: Dict[str, Any]):
        return item_dao.update(item_id, data)

    def delete(self, item_id: int):
        return item_dao.delete(item_id)

    def get_units(self, item_id: int) -> List[Dict]:
        return records(item_dao.get_units(item_id), 'units')

    def add_unit(self, item_id: int, unit_name: str, conversion_factor: float):
        return item_dao.add_unit(item_id, unit_name, conversion_factor)

    def clear_units(self, item_id: int):
        return item_dao.clear_units(item_id)

    def sold_quantities(self, item_ids: list[int]) -> Dict[int, Decimal]:
        if not item_ids:
            return {}
        ids = [int(x) for x in item_ids if x is not None]
        if not ids:
            return {}

        result = {i: Decimal('0') for i in ids}
        try:
            conn = item_dao.repo.db.get_connection()
            placeholders = ','.join('?' for _ in ids)
            rows = conn.execute(f"""
                SELECT il.item_id, COALESCE(SUM(CAST(COALESCE(NULLIF(il.quantity_in_base,''), il.quantity, '0') AS REAL)), 0) AS qty
                FROM invoice_lines il
                JOIN invoices inv ON inv.id = il.invoice_id
                WHERE inv.type = 'sale'
                  AND COALESCE(inv.deleted_at, '') = ''
                  AND il.item_id IN ({placeholders})
                GROUP BY il.item_id
            """, ids).fetchall()
            for row in rows:
                result[int(row['item_id'])] = Decimal(str(row['qty'] or 0))

            try:
                rrows = conn.execute(f"""
                    SELECT srl.item_id, COALESCE(SUM(CAST(COALESCE(NULLIF(srl.quantity_in_base,''), srl.quantity, '0') AS REAL)), 0) AS qty
                    FROM sales_return_lines srl
                    JOIN sales_returns sr ON sr.id = srl.sales_return_id
                    WHERE COALESCE(sr.status, 'active') != 'cancelled'
                      AND COALESCE(sr.deleted_at, '') = ''
                      AND srl.item_id IN ({placeholders})
                    GROUP BY srl.item_id
                """, ids).fetchall()
                for row in rrows:
                    item_id = int(row['item_id'])
                    result[item_id] = result.get(item_id, Decimal('0')) - Decimal(str(row['qty'] or 0))
                    if result[item_id] < 0:
                        result[item_id] = Decimal('0')
            except Exception:
                pass
            return result
        except Exception:
            return result

    def is_remote(self) -> bool:
        return False


class LocalCategoryGateway(CategoryGateway):
    def list(self, search: str | None = None, include_inactive: bool = False,
             include_deleted: bool = False) -> List[Dict]:
        return records(category_dao.get_all(search=search, include_inactive=include_inactive, include_deleted=include_deleted), 'categories')

    def get(self, category_id: int) -> Optional[Dict]:
        category = category_dao.get_by_id(category_id)
        return category if isinstance(category, dict) else None

    def create(self, data: Dict[str, Any]) -> int:
        return category_dao.add(
            data.get('name'), data.get('parent_id'), data.get('description', ''),
            data.get('color', '#64748B'), data.get('icon', 'folder'), data.get('is_active', 1)
        )

    def update(self, category_id: int, data: Dict[str, Any]):
        return category_dao.update(category_id, data)

    def delete(self, category_id: int):
        return category_dao.delete(category_id)

    def restore(self, category_id: int):
        return category_dao.restore(category_id)

    def is_remote(self) -> bool:
        return False
