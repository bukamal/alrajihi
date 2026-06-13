# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List, Optional

from core.services.audit_service import audit_service
from core.services.branch_service import branch_service
from gateways.warehouse_gateway import create_warehouse_gateway


class WarehouseService:
    def __init__(self):
        self.gateway = create_warehouse_gateway()

    def bootstrap(self) -> None:
        self.gateway.bootstrap()

    def warehouses(self, include_archived: bool = False) -> List[Dict]:
        return self.gateway.list(include_archived=include_archived)

    def warehouse_by_id(self, warehouse_id: int) -> Optional[Dict]:
        wh = self.gateway.get(warehouse_id)
        return wh if isinstance(wh, dict) else None

    def add_warehouse(self, data: Dict) -> int:
        data = self._validate_payload(data)
        wh_id = self.gateway.create(data)
        audit_service.log('CREATE', 'WAREHOUSE', wh_id, new_values=data, details='إنشاء مستودع')
        return wh_id

    def update_warehouse(self, warehouse_id: int, data: Dict) -> None:
        old = self.warehouse_by_id(warehouse_id)
        data = self._validate_payload(data)
        self.gateway.update(warehouse_id, data)
        audit_service.log('UPDATE', 'WAREHOUSE', warehouse_id, old_values=old, new_values=self.warehouse_by_id(warehouse_id) or data, details='تعديل مستودع')

    def archive_warehouse(self, warehouse_id: int) -> None:
        old = self.warehouse_by_id(warehouse_id)
        self.gateway.archive(warehouse_id)
        audit_service.log('SOFT_DELETE', 'WAREHOUSE', warehouse_id, old_values=old, details='أرشفة مستودع')

    def balances(self, search: str | None = None, warehouse_id: int | None = None, limit: int | None = None, offset: int | None = None) -> List[Dict]:
        return self.gateway.balances(search=search, warehouse_id=warehouse_id, limit=limit, offset=offset)

    def balance_count(self, search: str | None = None, warehouse_id: int | None = None) -> int:
        return int(self.gateway.balance_count(search=search, warehouse_id=warehouse_id) or 0)

    def movements(self, item_id: int | None = None, warehouse_id: int | None = None, limit: int = 100) -> List[Dict]:
        return self.gateway.movements(item_id=item_id, warehouse_id=warehouse_id, limit=limit)

    def default_warehouse_id(self) -> int | None:
        try:
            return self.gateway.default_warehouse_id()
        except Exception as exc:
            print(f"⚠️ تعذر جلب المستودع الافتراضي من الخادم: {exc}")
            return None

    def default_warehouse(self) -> Optional[Dict]:
        try:
            return self.gateway.default_warehouse()
        except Exception as exc:
            print(f"⚠️ تعذر جلب بيانات المستودع الافتراضي من الخادم: {exc}")
            return None

    def available_qty(self, item_id: int, warehouse_id: int | None = None):
        try:
            return self.gateway.available_qty(item_id, warehouse_id)
        except Exception as exc:
            print(f"⚠️ تعذر جلب الرصيد المتاح من الخادم: {exc}")
            return None


    def record_movement(self, item_id, warehouse_id, movement_type, quantity, unit_cost='0', reference_type=None, reference_id=None, notes=''):
        movement_id = self.gateway.record_movement(item_id, warehouse_id, movement_type, quantity, unit_cost, reference_type, reference_id, notes)
        # Phase 25: local shadow ledger for direct warehouse movements. Remote
        # mode is posted server-side; invoice/return references have dedicated
        # ledger hooks to avoid duplicate entries.
        if not self.gateway.is_remote() and reference_type not in ('invoice', 'sales_return', 'purchase_return'):
            self._record_warehouse_ledger_entry(
                item_id=item_id,
                warehouse_id=warehouse_id,
                movement_type=movement_type,
                direction=self._direction_from_quantity(quantity),
                quantity=quantity,
                unit_cost=unit_cost,
                reference_type=reference_type or 'warehouse_movement',
                reference_id=reference_id or movement_id,
                source_table='warehouse_movements',
                source_id=movement_id,
                notes=notes,
            )
        return movement_id


    def _direction_from_quantity(self, quantity) -> str:
        from decimal import Decimal
        try:
            q = Decimal(str(quantity or 0))
        except Exception:
            q = Decimal('0')
        if q > 0:
            return 'in'
        if q < 0:
            return 'out'
        return 'neutral'

    def _record_warehouse_ledger_entry(self, item_id, warehouse_id, movement_type, direction, quantity, unit_cost='0', reference_type=None, reference_id=None, source_table='warehouse_movements', source_id=None, notes='') -> None:
        try:
            from decimal import Decimal
            from core.services.inventory_service import inventory_service
            qty = abs(Decimal(str(quantity or 0)))
            inventory_service.record_ledger_entry(
                item_id=item_id,
                warehouse_id=warehouse_id,
                movement_type=movement_type,
                direction=direction,
                quantity=str(qty),
                unit_cost=str(unit_cost or 0),
                reference_type=reference_type or 'warehouse_movement',
                reference_id=reference_id,
                source_table=source_table,
                source_id=source_id,
                notes=notes,
            )
        except Exception as exc:
            print(f"⚠️ فشل تسجيل دفتر المخزون لحركة مستودع: {exc}")

    def _record_transfer_ledger_entries(self, transfer_id: int, data: Dict) -> None:
        from decimal import Decimal
        item_id = data.get('item_id')
        from_wh = data.get('from_warehouse_id')
        to_wh = data.get('to_warehouse_id')
        qty = abs(Decimal(str(data.get('quantity') or 0)))
        unit_cost = data.get('unit_cost', data.get('cost', 0))
        if not item_id or not from_wh or not to_wh or qty <= 0:
            return
        self._record_warehouse_ledger_entry(item_id, from_wh, 'transfer_out', 'out', qty, unit_cost, 'warehouse_transfer', transfer_id, 'warehouse_transfers', transfer_id, 'دفتر مخزون تحويل مستودعي - خروج')
        self._record_warehouse_ledger_entry(item_id, to_wh, 'transfer_in', 'in', qty, unit_cost, 'warehouse_transfer', transfer_id, 'warehouse_transfers', transfer_id, 'دفتر مخزون تحويل مستودعي - دخول')

    def _record_transfer_cancel_ledger_entries(self, transfer_id: int, transfer: Dict) -> None:
        from decimal import Decimal
        item_id = transfer.get('item_id')
        from_wh = transfer.get('from_warehouse_id')
        to_wh = transfer.get('to_warehouse_id')
        qty = abs(Decimal(str(transfer.get('quantity') or 0)))
        unit_cost = transfer.get('unit_cost', 0)
        if not item_id or not from_wh or not to_wh or qty <= 0:
            return
        self._record_warehouse_ledger_entry(item_id, to_wh, 'transfer_cancel_out', 'out', qty, unit_cost, 'warehouse_transfer_cancel', transfer_id, 'warehouse_transfers', transfer_id, 'عكس دفتر مخزون تحويل مستودعي - خروج من الوجهة')
        self._record_warehouse_ledger_entry(item_id, from_wh, 'transfer_cancel_in', 'in', qty, unit_cost, 'warehouse_transfer_cancel', transfer_id, 'warehouse_transfers', transfer_id, 'عكس دفتر مخزون تحويل مستودعي - دخول إلى المصدر')

    def reverse_reference(self, reference_type, reference_id) -> None:
        self.gateway.reverse_reference(reference_type, reference_id)

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
            conv_factor = Decimal(str(line.get('conversion_factor', 1) or 1))
            if conv_factor <= 0:
                conv_factor = Decimal('1')
            display_qty = Decimal(str(line.get('quantity', 0) or 0))
            qty = Decimal(str(line.get('base_qty', line.get('quantity_in_base', display_qty * conv_factor)) or 0))
            raw_unit_cost = Decimal(str(line.get('unit_cost', line.get('unit_price', 0)) or 0))
            unit_cost = raw_unit_cost / conv_factor if inv_type == 'purchase' else raw_unit_cost
            if inv_type == 'sale':
                movement_type = 'invoice_sale_out'
                direction = 'out'
                signed_qty = -abs(Decimal(str(qty or 0)))
                note = 'صرف فاتورة بيع من المستودع'
            elif inv_type == 'purchase':
                movement_type = 'invoice_purchase_in'
                direction = 'in'
                signed_qty = abs(Decimal(str(qty or 0)))
                note = 'استلام فاتورة شراء إلى المستودع'
            else:
                continue
            self.gateway.record_movement(item_id, wh_id, movement_type, signed_qty, unit_cost, 'invoice', invoice_id, note)
            self._record_invoice_ledger_entry(
                invoice_id=invoice_id,
                item_id=item_id,
                warehouse_id=wh_id,
                movement_type=movement_type,
                direction=direction,
                quantity=abs(Decimal(str(qty or 0))),
                unit_cost=unit_cost,
                notes=note,
            )

    def reverse_invoice_movements(self, invoice_id: int, invoice_data: Dict | None = None) -> None:
        if invoice_data:
            self._record_invoice_ledger_reversal(invoice_id, invoice_data)
        else:
            self._record_invoice_ledger_reversal_from_existing(invoice_id)
        self.gateway.reverse_reference('invoice', invoice_id)

    def _record_invoice_ledger_entry(self, invoice_id: int, item_id, warehouse_id, movement_type, direction, quantity, unit_cost, notes='') -> None:
        try:
            from core.services.inventory_service import inventory_service
            inventory_service.record_ledger_entry(
                item_id=item_id,
                warehouse_id=warehouse_id,
                movement_type=movement_type,
                direction=direction,
                quantity=str(quantity),
                unit_cost=str(unit_cost or 0),
                reference_type='invoice',
                reference_id=invoice_id,
                source_table='invoices',
                source_id=invoice_id,
                notes=notes,
            )
        except Exception as exc:
            print(f"⚠️ فشل تسجيل دفتر المخزون للفاتورة {invoice_id}: {exc}")

    def _record_invoice_ledger_reversal(self, invoice_id: int, invoice_data: Dict) -> None:
        from decimal import Decimal
        wh_id = invoice_data.get('warehouse_id') or self.default_warehouse_id()
        inv_type = invoice_data.get('type')
        if not wh_id or not invoice_data.get('lines'):
            return
        for line in invoice_data.get('lines') or []:
            item_id = line.get('item_id')
            if not item_id:
                continue
            conv_factor = Decimal(str(line.get('conversion_factor', 1) or 1))
            if conv_factor <= 0:
                conv_factor = Decimal('1')
            display_qty = Decimal(str(line.get('quantity', 0) or 0))
            qty = abs(Decimal(str(line.get('base_qty', line.get('quantity_in_base', display_qty * conv_factor)) or 0)))
            raw_unit_cost = Decimal(str(line.get('unit_cost', line.get('unit_price', 0)) or 0))
            unit_cost = raw_unit_cost / conv_factor if inv_type == 'purchase' else raw_unit_cost
            if inv_type == 'sale':
                self._record_invoice_ledger_entry(invoice_id, item_id, wh_id, 'invoice_sale_reversal', 'in', qty, unit_cost, 'عكس دفتر مخزون فاتورة بيع')
            elif inv_type == 'purchase':
                self._record_invoice_ledger_entry(invoice_id, item_id, wh_id, 'invoice_purchase_reversal', 'out', qty, unit_cost, 'عكس دفتر مخزون فاتورة شراء')

    def _record_invoice_ledger_reversal_from_existing(self, invoice_id: int) -> None:
        try:
            from core.services.inventory_service import inventory_service
            entries = inventory_service.ledger_entries(reference_type='invoice', reference_id=invoice_id, limit=500)
            for entry in entries:
                mt = str(entry.get('movement_type') or '')
                if mt.endswith('_reversal'):
                    continue
                direction = 'out' if entry.get('direction') == 'in' else 'in' if entry.get('direction') == 'out' else 'neutral'
                inventory_service.record_ledger_entry(
                    item_id=entry.get('item_id'),
                    warehouse_id=entry.get('warehouse_id'),
                    movement_type=f"{mt}_reversal" if mt else 'invoice_reversal',
                    direction=direction,
                    quantity=str(entry.get('quantity') or 0),
                    unit_cost=str(entry.get('unit_cost') or 0),
                    reference_type='invoice',
                    reference_id=invoice_id,
                    source_table='invoices',
                    source_id=invoice_id,
                    notes='عكس دفتر مخزون فاتورة',
                )
        except Exception as exc:
            print(f"⚠️ فشل عكس دفتر المخزون للفاتورة {invoice_id}: {exc}")



    def transfers(self, limit: int = 200) -> List[Dict]:
        return self.gateway.transfers(limit=limit)

    def create_transfer(self, data: Dict) -> int:
        transfer_id = self.gateway.create_transfer(data)
        if not self.gateway.is_remote():
            self._record_transfer_ledger_entries(transfer_id, data)
        audit_service.log('CREATE', 'WAREHOUSE_TRANSFER', transfer_id, new_values=data, details='إنشاء تحويل مستودعي')
        return transfer_id

    def cancel_transfer(self, transfer_id: int) -> None:
        old = next((t for t in self.transfers(limit=500) if int(t.get('id') or 0) == int(transfer_id)), None)
        self.gateway.cancel_transfer(transfer_id)
        if old and not self.gateway.is_remote():
            self._record_transfer_cancel_ledger_entries(transfer_id, old)
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
