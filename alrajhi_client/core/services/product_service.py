# -*- coding: utf-8 -*-
"""Product and category application service.

This service centralizes item/category operations that were historically called
from widgets and dialogs through DAOs directly.  It deliberately keeps the DAO
APIs intact for backward compatibility while giving UI code one stable facade.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal, InvalidOperation

from core.compat import records, pair
from core.services.audit_service import audit_service
from core.services.barcode_service import barcode_service
from database.dao.item_dao import item_dao
from database.dao.category_dao import category_dao


class ProductService:
    """Facade for item, unit, and category operations used by the UI."""

    def _validate_item_barcode(self, barcode: str | None, item_id: int | None = None) -> str | None:
        info = barcode_service.validate(barcode, allow_empty=True)
        normalized = info.value if info else None
        if not normalized:
            return None
        existing = self.item_by_barcode(normalized)
        if existing and int(existing.get('id', 0)) != int(item_id or 0):
            raise ValueError(f"الباركود '{normalized}' مستخدم بالفعل للمادة: {existing.get('name', existing.get('id'))}")
        return normalized

    def generate_barcode(self, symbology: str = 'EAN13') -> str:
        symbology = (symbology or 'EAN13').upper()
        for _ in range(100):
            candidate = barcode_service.generate_code128() if symbology == 'CODE128' else barcode_service.generate_ean13()
            if not self.item_by_barcode(candidate):
                return candidate
        raise ValueError("تعذر توليد باركود غير مكرر. حاول مرة أخرى.")

    # ---------- Items ----------
    def items(self, search: str | None = None, limit: int | None = None, offset: int | None = None) -> List[Dict]:
        return records(item_dao.get_items(search=search, limit=limit, offset=offset), 'items')

    def items_pair(self, search: str | None = None, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict], int]:
        return pair(item_dao.get_items(search=search, limit=limit, offset=offset), 'items')

    def item_by_id(self, item_id: int) -> Optional[Dict]:
        item = item_dao.get_by_id(item_id)
        return item if isinstance(item, dict) else None

    def item_by_barcode(self, barcode: str) -> Optional[Dict]:
        item = item_dao.get_by_barcode(barcode)
        return item if isinstance(item, dict) else None

    def add_item(self, data: Dict[str, Any]) -> int:
        data = dict(data)
        data['barcode'] = self._validate_item_barcode(data.get('barcode'))
        item_id = item_dao.add(data)
        audit_service.log('CREATE', 'ITEM', item_id, new_values=data, details='إنشاء مادة')
        return item_id

    def update_item(self, item_id: int, data: Dict[str, Any]) -> None:
        old = self.item_by_id(item_id)
        data = dict(data)
        data['barcode'] = self._validate_item_barcode(data.get('barcode'), item_id=item_id)
        item_dao.update(item_id, data)
        new = self.item_by_id(item_id)
        audit_service.log('UPDATE', 'ITEM', item_id, old_values=old, new_values=new or data, details='تعديل مادة')

    def delete_item(self, item_id: int) -> None:
        old = self.item_by_id(item_id)
        item_dao.delete(item_id)
        audit_service.log('SOFT_DELETE', 'ITEM', item_id, old_values=old, details='أرشفة مادة')

    # ---------- Item units ----------
    def item_units(self, item_id: int) -> List[Dict]:
        return records(item_dao.get_units(item_id), 'units')

    def _normalize_unit_name(self, name: str) -> str:
        return " ".join(str(name or "").strip().split())

    def _parse_unit_factor(self, value) -> Decimal:
        text = str(value or '').strip()
        if not text:
            raise InvalidOperation
        arabic_digits = str.maketrans('٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹٫٬', '01234567890123456789..')
        text = text.translate(arabic_digits).replace(' ', '').replace(',', '.')
        return Decimal(text)

    def _validate_units_payload(self, item_id: int, units: List[Dict[str, Any]], base_unit: str = None) -> List[Dict[str, str]]:
        item = self.item_by_id(item_id) or {}
        base_unit = self._normalize_unit_name(base_unit if base_unit is not None else (item.get('unit') or 'قطعة'))
        seen = set()
        clean_units: List[Dict[str, str]] = []
        for unit in units or []:
            name = self._normalize_unit_name(unit.get('unit_name', ''))
            if not name:
                continue
            key = name.casefold()
            if base_unit and key == base_unit.casefold():
                raise ValueError(f"لا يجوز إضافة الوحدة الفرعية '{name}' لأنها مطابقة للوحدة الأساسية")
            if key in seen:
                raise ValueError(f"الوحدة الفرعية '{name}' مكررة")
            seen.add(key)
            try:
                factor = self._parse_unit_factor(unit.get('conversion_factor', '1'))
            except (InvalidOperation, ValueError, TypeError):
                raise ValueError(f"عامل التحويل للوحدة '{name}' غير صالح")
            if factor <= 0:
                raise ValueError(f"عامل التحويل للوحدة '{name}' يجب أن يكون أكبر من صفر")
            clean_units.append({'unit_name': name, 'conversion_factor': str(factor)})
        return clean_units

    def add_unit(self, item_id: int, unit_name: str, conversion_factor: float) -> None:
        clean = self._validate_units_payload(item_id, [{'unit_name': unit_name, 'conversion_factor': conversion_factor}])
        if clean:
            item_dao.add_unit(item_id, clean[0]['unit_name'], clean[0]['conversion_factor'])

    def clear_units(self, item_id: int) -> None:
        item_dao.clear_units(item_id)

    def replace_units(self, item_id: int, units: List[Dict[str, Any]], base_unit: str = None) -> None:
        old_units = self.item_units(item_id)
        saved_units = self._validate_units_payload(item_id, units, base_unit=base_unit)
        self.clear_units(item_id)
        for unit in saved_units:
            item_dao.add_unit(item_id, unit['unit_name'], unit['conversion_factor'])
        audit_service.log(
            'UPDATE_UNITS', 'ITEM', item_id,
            old_values={'units': old_units},
            new_values={'units': saved_units},
            details='تعديل وحدات المادة'
        )


    def sold_quantities(self, item_ids: list[int]) -> Dict[int, Decimal]:
        """Return net sold quantities per item in base unit.

        Net sold = sale invoice quantities - non-cancelled sales returns.
        The method is defensive: if a legacy database does not yet contain
        returns tables, it still returns sales totals without breaking the UI.
        """
        from decimal import Decimal
        if not item_ids:
            return {}
        ids = [int(x) for x in item_ids if x is not None]
        if not ids:
            return {}
        result = {i: Decimal('0') for i in ids}
        try:
            db = item_dao.repo.db
            if db.is_remote():
                return result
            conn = db.get_connection()
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

    # ---------- Categories ----------
    def categories(self, search: str | None = None, include_inactive: bool = False, include_deleted: bool = False) -> List[Dict]:
        return records(category_dao.get_all(search=search, include_inactive=include_inactive, include_deleted=include_deleted), 'categories')

    def category_by_id(self, category_id: int) -> Optional[Dict]:
        return category_dao.get_by_id(category_id)

    def add_category(self, data_or_name, parent_id=None, description: str = '', color: str = '#64748B', icon: str = 'folder', is_active: int = 1) -> int:
        if isinstance(data_or_name, dict):
            data = dict(data_or_name)
            category_id = category_dao.add(
                data.get('name'), data.get('parent_id'), data.get('description', ''),
                data.get('color', '#64748B'), data.get('icon', 'folder'), data.get('is_active', 1)
            )
            new_values = data
        else:
            category_id = category_dao.add(data_or_name, parent_id, description, color, icon, is_active)
            new_values = {'name': data_or_name, 'parent_id': parent_id, 'description': description, 'color': color, 'icon': icon, 'is_active': is_active}
        audit_service.log('CREATE', 'CATEGORY', category_id, new_values=new_values, details='إنشاء تصنيف')
        return category_id

    def update_category(self, category_id: int, data_or_name, **kwargs) -> None:
        old = self.category_by_id(category_id)
        if isinstance(data_or_name, dict):
            category_dao.update(category_id, data_or_name)
            new_values = self.category_by_id(category_id) or data_or_name
        else:
            category_dao.update(category_id, data_or_name, **kwargs)
            new_values = self.category_by_id(category_id) or {'id': category_id, 'name': data_or_name, **kwargs}
        audit_service.log('UPDATE', 'CATEGORY', category_id, old_values=old, new_values=new_values, details='تعديل تصنيف')

    def delete_category(self, category_id: int) -> None:
        old = self.category_by_id(category_id)
        category_dao.delete(category_id)
        audit_service.log('SOFT_DELETE', 'CATEGORY', category_id, old_values=old, details='أرشفة تصنيف')

    def restore_category(self, category_id: int) -> None:
        old = self.category_by_id(category_id)
        category_dao.restore(category_id)
        audit_service.log('RESTORE', 'CATEGORY', category_id, old_values=old, new_values=self.category_by_id(category_id), details='استعادة تصنيف')


product_service = ProductService()
