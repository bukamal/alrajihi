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

    def add_unit(self, item_id: int, unit_name: str, conversion_factor: float, barcode: str | None = None, notes: str = ''):
        return item_dao.add_unit(item_id, unit_name, conversion_factor, barcode, notes)

    def clear_units(self, item_id: int):
        return item_dao.clear_units(item_id)

    def get_variants(self, item_id: int) -> List[Dict]:
        return records(item_dao.get_variants(item_id), 'variants')

    def get_variant_by_barcode(self, barcode: str) -> Optional[Dict]:
        variant = item_dao.get_variant_by_barcode(barcode)
        return variant if isinstance(variant, dict) else None

    def add_variant(self, item_id: int, data: Dict[str, Any]) -> int:
        return item_dao.add_variant(item_id, data)

    def update_variant(self, variant_id: int, data: Dict[str, Any]):
        return item_dao.update_variant(variant_id, data)

    def delete_variant(self, variant_id: int):
        return item_dao.delete_variant(variant_id)

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


    def activity_summary(self, item_id: int) -> Dict[str, Any]:
        """Return material usage counts without leaking SQL above the gateway."""
        item_id = int(item_id or 0)
        summary = {
            'invoice_lines': 0,
            'purchase_lines': 0,
            'sales_return_lines': 0,
            'purchase_return_lines': 0,
            'inventory_movements': 0,
            'bom_products': 0,
            'bom_lines': 0,
            'production_orders': 0,
            'production_consumptions': 0,
            'production_outputs': 0,
        }
        if not item_id:
            summary['blocking_total'] = 0
            summary['has_movements'] = False
            return summary
        def count(conn, sql, params):
            try:
                row = conn.execute(sql, params).fetchone()
                return int(row[0] if row else 0)
            except Exception:
                return 0
        try:
            conn = item_dao.repo.db.get_connection()
            summary['invoice_lines'] = count(conn, "SELECT COUNT(*) FROM invoice_lines WHERE item_id=?", (item_id,))
            summary['purchase_lines'] = count(conn, "SELECT COUNT(*) FROM purchase_invoice_lines WHERE item_id=?", (item_id,))
            summary['sales_return_lines'] = count(conn, "SELECT COUNT(*) FROM sales_return_lines WHERE item_id=?", (item_id,))
            summary['purchase_return_lines'] = count(conn, "SELECT COUNT(*) FROM purchase_return_lines WHERE item_id=?", (item_id,))
            summary['inventory_movements'] = count(conn, "SELECT COUNT(*) FROM inventory_movements WHERE item_id=? AND movement_type <> 'opening'", (item_id,))
            summary['bom_products'] = count(conn, "SELECT COUNT(*) FROM bom WHERE product_id=?", (item_id,))
            summary['bom_lines'] = count(conn, "SELECT COUNT(*) FROM bom_lines WHERE item_id=?", (item_id,))
            summary['production_orders'] = count(conn, "SELECT COUNT(*) FROM production_orders WHERE product_id=?", (item_id,))
            summary['production_consumptions'] = count(conn, "SELECT COUNT(*) FROM production_consumptions WHERE item_id=?", (item_id,))
            summary['production_outputs'] = count(conn, "SELECT COUNT(*) FROM production_outputs WHERE item_id=?", (item_id,))
        except Exception:
            pass
        summary['blocking_total'] = sum(int(v or 0) for k, v in summary.items() if k not in ('blocking_total', 'has_movements'))
        summary['has_movements'] = bool(summary['blocking_total'])
        return summary

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


    def activity_summary(self, item_id: int) -> Dict[str, Any]:
        """Return material usage counts without leaking SQL above the gateway."""
        item_id = int(item_id or 0)
        summary = {
            'invoice_lines': 0,
            'purchase_lines': 0,
            'sales_return_lines': 0,
            'purchase_return_lines': 0,
            'inventory_movements': 0,
            'bom_products': 0,
            'bom_lines': 0,
            'production_orders': 0,
            'production_consumptions': 0,
            'production_outputs': 0,
        }
        if not item_id:
            summary['blocking_total'] = 0
            summary['has_movements'] = False
            return summary
        def count(conn, sql, params):
            try:
                row = conn.execute(sql, params).fetchone()
                return int(row[0] if row else 0)
            except Exception:
                return 0
        try:
            conn = item_dao.repo.db.get_connection()
            summary['invoice_lines'] = count(conn, "SELECT COUNT(*) FROM invoice_lines WHERE item_id=?", (item_id,))
            summary['purchase_lines'] = count(conn, "SELECT COUNT(*) FROM purchase_invoice_lines WHERE item_id=?", (item_id,))
            summary['sales_return_lines'] = count(conn, "SELECT COUNT(*) FROM sales_return_lines WHERE item_id=?", (item_id,))
            summary['purchase_return_lines'] = count(conn, "SELECT COUNT(*) FROM purchase_return_lines WHERE item_id=?", (item_id,))
            summary['inventory_movements'] = count(conn, "SELECT COUNT(*) FROM inventory_movements WHERE item_id=? AND movement_type <> 'opening'", (item_id,))
            summary['bom_products'] = count(conn, "SELECT COUNT(*) FROM bom WHERE product_id=?", (item_id,))
            summary['bom_lines'] = count(conn, "SELECT COUNT(*) FROM bom_lines WHERE item_id=?", (item_id,))
            summary['production_orders'] = count(conn, "SELECT COUNT(*) FROM production_orders WHERE product_id=?", (item_id,))
            summary['production_consumptions'] = count(conn, "SELECT COUNT(*) FROM production_consumptions WHERE item_id=?", (item_id,))
            summary['production_outputs'] = count(conn, "SELECT COUNT(*) FROM production_outputs WHERE item_id=?", (item_id,))
        except Exception:
            pass
        summary['blocking_total'] = sum(int(v or 0) for k, v in summary.items() if k not in ('blocking_total', 'has_movements'))
        summary['has_movements'] = bool(summary['blocking_total'])
        return summary

    def is_remote(self) -> bool:
        return False
