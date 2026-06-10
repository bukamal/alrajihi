# -*- coding: utf-8 -*-
"""Product and category application service.

This service centralizes item/category operations that were historically called
from widgets and dialogs through DAOs directly.  It deliberately keeps the DAO
APIs intact for backward compatibility while giving UI code one stable facade.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

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

    def add_unit(self, item_id: int, unit_name: str, conversion_factor: float) -> None:
        item_dao.add_unit(item_id, unit_name, conversion_factor)

    def clear_units(self, item_id: int) -> None:
        item_dao.clear_units(item_id)

    def replace_units(self, item_id: int, units: List[Dict[str, Any]]) -> None:
        self.clear_units(item_id)
        for unit in units:
            name = str(unit.get('unit_name', '')).strip()
            if not name:
                continue
            factor = float(unit.get('conversion_factor', 1))
            self.add_unit(item_id, name, factor)

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
