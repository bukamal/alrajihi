# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List, Optional

from core.compat import records
from core.services.audit_service import audit_service
from core.services.branch_service import branch_service
from database.dao.warehouse_dao import warehouse_dao


class WarehouseService:
    def bootstrap(self) -> None:
        warehouse_dao.bootstrap_defaults()

    def warehouses(self, include_archived: bool = False) -> List[Dict]:
        return records(warehouse_dao.get_all(include_archived=include_archived), 'warehouses')

    def warehouse_by_id(self, warehouse_id: int) -> Optional[Dict]:
        wh = warehouse_dao.get_by_id(warehouse_id)
        return wh if isinstance(wh, dict) else None

    def add_warehouse(self, data: Dict) -> int:
        data = self._validate_payload(data)
        wh_id = warehouse_dao.add(data)
        audit_service.log('CREATE', 'WAREHOUSE', wh_id, new_values=data, details='إنشاء مستودع')
        return wh_id

    def update_warehouse(self, warehouse_id: int, data: Dict) -> None:
        old = self.warehouse_by_id(warehouse_id)
        data = self._validate_payload(data)
        warehouse_dao.update(warehouse_id, data)
        audit_service.log('UPDATE', 'WAREHOUSE', warehouse_id, old_values=old, new_values=self.warehouse_by_id(warehouse_id) or data, details='تعديل مستودع')

    def archive_warehouse(self, warehouse_id: int) -> None:
        old = self.warehouse_by_id(warehouse_id)
        warehouse_dao.delete(warehouse_id)
        audit_service.log('SOFT_DELETE', 'WAREHOUSE', warehouse_id, old_values=old, details='أرشفة مستودع')

    def balances(self, search: str | None = None, warehouse_id: int | None = None, limit: int | None = None, offset: int | None = None) -> List[Dict]:
        return records(warehouse_dao.balances(search=search, warehouse_id=warehouse_id, limit=limit, offset=offset), 'balances')

    def balance_count(self, search: str | None = None, warehouse_id: int | None = None) -> int:
        return int(warehouse_dao.balance_count(search=search, warehouse_id=warehouse_id) or 0)

    def movements(self, item_id: int | None = None, warehouse_id: int | None = None, limit: int = 100) -> List[Dict]:
        return records(warehouse_dao.movements(item_id=item_id, warehouse_id=warehouse_id, limit=limit), 'movements')

    def default_warehouse_id(self) -> int | None:
        return warehouse_dao.default_warehouse_id()

    def default_warehouse(self) -> Optional[Dict]:
        return warehouse_dao.default_warehouse()

    def available_qty(self, item_id: int, warehouse_id: int | None = None):
        return warehouse_dao.available_qty(item_id, warehouse_id)


    def record_movement(self, item_id, warehouse_id, movement_type, quantity, unit_cost='0', reference_type=None, reference_id=None, notes=''):
        return warehouse_dao.record_movement(item_id, warehouse_id, movement_type, quantity, unit_cost, reference_type, reference_id, notes)

    def reverse_reference(self, reference_type, reference_id) -> None:
        warehouse_dao.reverse_reference(reference_type, reference_id)

    def record_invoice_movements(self, invoice_id: int, invoice_data: Dict) -> None:
        from decimal import Decimal
        wh_id = invoice_data.get('warehouse_id') or self.default_warehouse_id()
        inv_type = invoice_data.get('type')
        if not wh_id or not invoice_data.get('lines'):
            return
        for line in invoice_data.get('lines') or []:
            item_id = line.get('item_id')
            if not item_id:
                continue
            qty = line.get('base_qty', line.get('quantity_in_base', line.get('quantity', 0)))
            unit_cost = line.get('unit_cost_base', line.get('average_cost', line.get('unit_price', 0)))
            if inv_type == 'sale':
                movement_type = 'invoice_sale_out'
                signed_qty = -abs(Decimal(str(qty or 0)))
                try:
                    from core.services.product_service import product_service
                    item = product_service.item_by_id(int(item_id)) or {}
                    unit_cost = item.get('average_cost', unit_cost)
                except Exception:
                    pass
                note = 'صرف فاتورة بيع من المستودع'
            elif inv_type == 'purchase':
                movement_type = 'invoice_purchase_in'
                signed_qty = abs(Decimal(str(qty or 0)))
                note = 'استلام فاتورة شراء إلى المستودع'
            else:
                continue
            warehouse_dao.record_movement(item_id, wh_id, movement_type, signed_qty, unit_cost, 'invoice', invoice_id, note)

    def reverse_invoice_movements(self, invoice_id: int) -> None:
        warehouse_dao.reverse_reference('invoice', invoice_id)



    def transfers(self, limit: int = 200) -> List[Dict]:
        return records(warehouse_dao.transfers(limit=limit), 'transfers')

    def create_transfer(self, data: Dict) -> int:
        transfer_id = warehouse_dao.create_transfer(data)
        audit_service.log('CREATE', 'WAREHOUSE_TRANSFER', transfer_id, new_values=data, details='إنشاء تحويل مستودعي')
        return transfer_id

    def cancel_transfer(self, transfer_id: int) -> None:
        old = next((t for t in self.transfers(limit=500) if int(t.get('id') or 0) == int(transfer_id)), None)
        warehouse_dao.cancel_transfer(transfer_id)
        audit_service.log('REVERSE', 'WAREHOUSE_TRANSFER', transfer_id, old_values=old, details='إلغاء تحويل مستودعي')

    def _validate_payload(self, data: Dict) -> Dict:
        payload = dict(data or {})
        name = str(payload.get('name', '')).strip()
        if not name:
            raise ValueError('اسم المستودع مطلوب')
        payload['name'] = name
        payload['code'] = str(payload.get('code', '')).strip()
        payload['location'] = str(payload.get('location', '')).strip()
        payload['notes'] = str(payload.get('notes', '')).strip()
        payload['branch_id'] = payload.get('branch_id') or branch_service.default_branch_id()
        payload['is_active'] = 1 if payload.get('is_active', 1) else 0
        return payload


warehouse_service = WarehouseService()
