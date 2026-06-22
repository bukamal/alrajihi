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
from gateways.product_gateway import create_product_gateways


class ProductService:
    """Facade for item, unit, and category operations used by the UI."""

    def __init__(self):
        self.item_gateway, self.category_gateway = create_product_gateways()


    def _validate_item_barcode(self, barcode: str | None, item_id: int | None = None) -> str | None:
        info = barcode_service.validate(barcode, allow_empty=True)
        normalized = info.value if info else None
        if not normalized:
            return None
        existing = self.item_by_barcode(normalized)
        if existing:
            same_item = int(existing.get('id', 0)) == int(item_id or 0)
            if not same_item or existing.get('barcode_scope') == 'unit':
                raise ValueError(f"الباركود '{normalized}' مستخدم بالفعل للمادة: {existing.get('name', existing.get('id'))}")
        return normalized

    def _normalize_unit_barcode(self, barcode: str | None) -> str | None:
        info = barcode_service.validate(barcode, allow_empty=True)
        return info.value if info and info.value else None

    def _validate_unit_barcodes(self, item_id: int, base_barcode: str | None, units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize and validate sub-unit barcodes without changing API keys.

        A barcode can identify either the base material or one of its units, but
        it must not identify two different materials/units.  During an item
        update we allow a currently existing barcode that belongs to the same
        item because replace_units() deletes/reinserts unit rows atomically.
        """
        normalized_units: List[Dict[str, Any]] = []
        seen = set()
        base_value = str(base_barcode or '').strip()
        if base_value:
            seen.add(base_value)
        for unit in units or []:
            row = dict(unit or {})
            value = self._normalize_unit_barcode(row.get('barcode') or row.get('unit_barcode'))
            if value:
                if value in seen:
                    raise ValueError(f"الباركود '{value}' مكرر بين المادة أو وحداتها")
                existing = self.item_by_barcode(value)
                if existing and int(existing.get('id', 0)) != int(item_id or 0):
                    raise ValueError(f"الباركود '{value}' مستخدم بالفعل للمادة: {existing.get('name', existing.get('id'))}")
                seen.add(value)
            row['barcode'] = value
            row['unit_barcode'] = value
            normalized_units.append(row)
        return normalized_units

    def generate_barcode(self, symbology: str = 'EAN13', prefix: str | None = None) -> str:
        symbology = (symbology or 'EAN13').upper()
        for _ in range(100):
            candidate = (
                barcode_service.generate_code128(prefix or 'ITM')
                if symbology == 'CODE128'
                else barcode_service.generate_ean13(prefix or '290')
            )
            if not self.item_by_barcode(candidate):
                return candidate
        raise ValueError("تعذر توليد باركود غير مكرر. حاول مرة أخرى.")

    # ---------- Items ----------
    def items(self, search: str | None = None, limit: int | None = None, offset: int | None = None) -> List[Dict]:
        return records(self.item_gateway.list(search=search, limit=limit, offset=offset), 'items')

    def items_pair(self, search: str | None = None, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict], int]:
        return pair(self.item_gateway.list(search=search, limit=limit, offset=offset), 'items')

    def item_by_id(self, item_id: int) -> Optional[Dict]:
        item = self.item_gateway.get(item_id)
        return item if isinstance(item, dict) else None

    def item_by_barcode(self, barcode: str) -> Optional[Dict]:
        item = self.item_gateway.get_by_barcode(barcode)
        return item if isinstance(item, dict) else None

    def add_item(self, data: Dict[str, Any]) -> int:
        data = dict(data)
        data['barcode'] = self._validate_item_barcode(data.get('barcode'))
        if data.get('units'):
            data['units'] = self._validate_unit_barcodes(0, data.get('barcode'), data.get('units') or [])
        item_id = self.item_gateway.create(data)
        # Persist sub-units supplied by document/service callers in the same
        # application boundary.  Older UI flows called replace_units() after
        # add_item(), but headless/import/API flows can legitimately submit
        # the full material payload at once.
        units = data.get('units') or []
        if units:
            self.replace_units(item_id, units)
        audit_service.log('CREATE', 'ITEM', item_id, new_values=data, details='إنشاء مادة')
        return item_id

    def update_item(self, item_id: int, data: Dict[str, Any]) -> None:
        old = self.item_by_id(item_id)
        data = dict(data)
        data['barcode'] = self._validate_item_barcode(data.get('barcode'), item_id=item_id)
        if data.get('units'):
            data['units'] = self._validate_unit_barcodes(item_id, data.get('barcode'), data.get('units') or [])
        self.item_gateway.update(item_id, data)
        new = self.item_by_id(item_id)
        audit_service.log('UPDATE', 'ITEM', item_id, old_values=old, new_values=new or data, details='تعديل مادة')

    def delete_item(self, item_id: int) -> None:
        old = self.item_by_id(item_id)
        self.item_gateway.delete(item_id)
        audit_service.log('SOFT_DELETE', 'ITEM', item_id, old_values=old, details='أرشفة مادة')

    # ---------- Item units ----------
    def item_units(self, item_id: int) -> List[Dict]:
        return records(self.item_gateway.get_units(item_id), 'units')

    def add_unit(self, item_id: int, unit_name: str, conversion_factor: float, barcode: str | None = None, notes: str = '') -> None:
        self.item_gateway.add_unit(item_id, unit_name, conversion_factor, barcode, notes)

    def clear_units(self, item_id: int) -> None:
        self.item_gateway.clear_units(item_id)

    def replace_units(self, item_id: int, units: List[Dict[str, Any]]) -> None:
        item = self.item_by_id(item_id) or {}
        units = self._validate_unit_barcodes(item_id, item.get('barcode'), units)
        # In remote mode item units are persisted atomically by POST/PUT /api/items.
        # Calling clear_units/add_unit would intentionally fail because the client
        # must not manipulate SQLite directly.
        try:
            if self.item_gateway.is_remote():
                audit_service.log(
                    'UPDATE_UNITS', 'ITEM', item_id,
                    new_values={'units': units},
                    details='تعديل وحدات المادة عبر الخادم'
                )
                return
        except Exception:
            pass
        old_units = self.item_units(item_id)
        self.clear_units(item_id)
        saved_units = []
        for unit in units:
            name = str(unit.get('unit_name', '')).strip()
            if not name:
                continue
            factor = float(unit.get('conversion_factor', 1))
            barcode = unit.get('barcode') or unit.get('unit_barcode') or None
            notes = str(unit.get('notes') or '')
            self.add_unit(item_id, name, factor, barcode, notes)
            saved_units.append({'unit_name': name, 'conversion_factor': factor, 'barcode': barcode, 'notes': notes})
        audit_service.log(
            'UPDATE_UNITS', 'ITEM', item_id,
            old_values={'units': old_units},
            new_values={'units': saved_units},
            details='تعديل وحدات المادة'
        )




    # ---------- Item variants / apparel foundation ----------
    def _normalize_variant_payload(self, item_id: int, data: Dict[str, Any], variant_id: int | None = None) -> Dict[str, Any]:
        item_id = int(item_id or 0)
        if not item_id or not self.item_by_id(item_id):
            raise ValueError("المادة الأصلية غير موجودة")
        row = dict(data or {})
        color = str(row.get('color') or '').strip()
        size = str(row.get('size') or '').strip()
        if not color and not size:
            raise ValueError("يجب تحديد لون أو مقاس واحد على الأقل")
        for existing in self.item_variants(item_id):
            if variant_id is not None and int(existing.get('id') or 0) == int(variant_id):
                continue
            if str(existing.get('color') or '').strip().casefold() == color.casefold() and str(existing.get('size') or '').strip().casefold() == size.casefold():
                raise ValueError(f"متغير المادة للون/المقاس موجود مسبقًا: {color} / {size}")
        barcode = self._normalize_unit_barcode(row.get('barcode'))
        if barcode:
            existing = self.item_by_barcode(barcode)
            if existing:
                same_variant = existing.get('barcode_scope') == 'variant' and int(existing.get('variant_id') or 0) == int(variant_id or 0)
                if not same_variant:
                    raise ValueError(f"الباركود '{barcode}' مستخدم بالفعل للمادة: {existing.get('name', existing.get('id'))}")
        normalized = {
            'color': color,
            'size': size,
            'sku': str(row.get('sku') or '').strip() or None,
            'barcode': barcode,
            'sale_price': str(row.get('sale_price') if row.get('sale_price') is not None else ''),
            'cost_price': str(row.get('cost_price') if row.get('cost_price') is not None else ''),
            'quantity': str(row.get('quantity') if row.get('quantity') is not None else '0'),
            'reorder_level': str(row.get('reorder_level') if row.get('reorder_level') is not None else '0'),
            'is_active': 1 if row.get('is_active', 1) not in (0, False, '0', 'false', 'False') else 0,
        }
        return normalized

    def item_variants(self, item_id: int) -> List[Dict]:
        return records(self.item_gateway.get_variants(int(item_id or 0)), 'variants')

    def item_variant_by_barcode(self, barcode: str) -> Optional[Dict]:
        variant = self.item_gateway.get_variant_by_barcode(barcode)
        return variant if isinstance(variant, dict) else None

    def add_variant(self, item_id: int, data: Dict[str, Any]) -> int:
        payload = self._normalize_variant_payload(item_id, data)
        variant_id = self.item_gateway.add_variant(int(item_id), payload)
        audit_service.log('CREATE', 'ITEM_VARIANT', variant_id, new_values={'item_id': item_id, **payload}, details='إنشاء متغير مادة')
        return variant_id

    def update_variant(self, variant_id: int, data: Dict[str, Any]) -> None:
        # Resolve parent item through the gateway list.  This keeps UI callers out
        # of SQL while preserving local/remote behavior.
        current = None
        for item in self.items(limit=None):
            for variant in self.item_variants(int(item.get('id') or 0)):
                if int(variant.get('id') or 0) == int(variant_id):
                    current = variant
                    break
            if current:
                break
        if not current:
            raise ValueError("متغير المادة غير موجود")
        old = dict(current)
        item_id = int(current.get('item_id') or 0)
        merged = {**current, **dict(data or {})}
        payload = self._normalize_variant_payload(item_id, merged, variant_id=int(variant_id))
        self.item_gateway.update_variant(int(variant_id), payload)
        audit_service.log('UPDATE', 'ITEM_VARIANT', variant_id, old_values=old, new_values=payload, details='تعديل متغير مادة')

    def delete_variant(self, variant_id: int) -> None:
        self.item_gateway.delete_variant(int(variant_id))
        audit_service.log('ARCHIVE', 'ITEM_VARIANT', variant_id, details='تعطيل متغير مادة')

    def item_activity_summary(self, item_id: int) -> Dict[str, Any]:
        """Return usage counts for a material through the active gateway."""
        try:
            summary = self.item_gateway.activity_summary(int(item_id or 0)) or {}
        except Exception:
            summary = {}
        if 'blocking_total' not in summary:
            summary['blocking_total'] = sum(int(v or 0) for k, v in summary.items() if k not in ('blocking_total', 'has_movements'))
        summary['has_movements'] = bool(summary.get('blocking_total'))
        return summary

    def item_has_activity(self, item_id: int) -> bool:
        return bool(self.item_activity_summary(item_id).get('has_movements'))

    def sold_quantities(self, item_ids: list[int]) -> Dict[int, Decimal]:
        """Return net sold quantities per item in base unit through ItemGateway."""
        return self.item_gateway.sold_quantities(item_ids)

    def _category_policy(self):
        from core.services.category_operation_policy import category_operation_policy
        return category_operation_policy

    # ---------- Categories ----------
    def categories(self, search: str | None = None, include_inactive: bool = False, include_deleted: bool = False) -> List[Dict]:
        self._category_policy().require(self._category_policy().OP_USE, context='categories.list')
        return records(self.category_gateway.list(search=search, include_inactive=include_inactive, include_deleted=include_deleted), 'categories')

    def category_by_id(self, category_id: int) -> Optional[Dict]:
        self._category_policy().require(self._category_policy().OP_USE, context='categories.get', payload={'category_id': category_id})
        return self.category_gateway.get(category_id)

    def add_category(self, data_or_name, parent_id=None, description: str = '', color: str = '#64748B', icon: str = 'folder', is_active: int = 1) -> int:
        self._category_policy().require(self._category_policy().OP_CREATE, context='categories.create')
        if isinstance(data_or_name, dict):
            data = dict(data_or_name)
            category_id = self.category_gateway.create(data)
            new_values = data
        else:
            category_id = self.category_gateway.create({'name': data_or_name, 'parent_id': parent_id, 'description': description, 'color': color, 'icon': icon, 'is_active': is_active})
            new_values = {'name': data_or_name, 'parent_id': parent_id, 'description': description, 'color': color, 'icon': icon, 'is_active': is_active}
        audit_service.log('CREATE', 'CATEGORY', category_id, new_values=new_values, details='إنشاء تصنيف')
        return category_id

    def update_category(self, category_id: int, data_or_name, **kwargs) -> None:
        self._category_policy().require(self._category_policy().OP_EDIT, context='categories.edit', payload={'category_id': category_id})
        old = self.category_by_id(category_id)
        if isinstance(data_or_name, dict):
            self.category_gateway.update(category_id, data_or_name)
            new_values = self.category_by_id(category_id) or data_or_name
        else:
            self.category_gateway.update(category_id, {'name': data_or_name, **kwargs})
            new_values = self.category_by_id(category_id) or {'id': category_id, 'name': data_or_name, **kwargs}
        audit_service.log('UPDATE', 'CATEGORY', category_id, old_values=old, new_values=new_values, details='تعديل تصنيف')

    def delete_category(self, category_id: int) -> None:
        self._category_policy().require(self._category_policy().OP_ARCHIVE, context='categories.archive', payload={'category_id': category_id})
        old = self.category_by_id(category_id)
        self.category_gateway.delete(category_id)
        audit_service.log('SOFT_DELETE', 'CATEGORY', category_id, old_values=old, details='أرشفة تصنيف')

    def restore_category(self, category_id: int) -> None:
        self._category_policy().require(self._category_policy().OP_RESTORE, context='categories.restore', payload={'category_id': category_id})
        old = self.category_by_id(category_id)
        self.category_gateway.restore(category_id)
        audit_service.log('RESTORE', 'CATEGORY', category_id, old_values=old, new_values=self.category_by_id(category_id), details='استعادة تصنيف')


product_service = ProductService()
