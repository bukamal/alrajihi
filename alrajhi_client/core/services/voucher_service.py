# -*- coding: utf-8 -*-
"""Voucher application service.

This facade keeps voucher UI code away from legacy DAO return-shape details and
party-name lookup mechanics while preserving the existing DAO/Repository APIs.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from core.compat import pair
from core.services.catalog_service import catalog_service
from gateways.voucher_gateway import create_voucher_gateway
from core.services.audit_service import audit_service
from core.services.branch_service import branch_service
from core.services.cashbox_service import cashbox_service


class VoucherService:
    def __init__(self, gateway=None):
        self.gateway = gateway or create_voucher_gateway()

    def _finance_policy(self):
        from core.services.finance_operation_policy import finance_operation_policy
        return finance_operation_policy

    def _require(self, operation_key: str, context: str = '', payload: Dict | None = None) -> None:
        self._finance_policy().require(operation_key, context=context, payload=payload or {})

    def list_vouchers(self, search: str | None = None, vtype: str | None = None,
                      limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict], int]:
        self._require('voucher_view', context='voucher:list', payload={'type': vtype})
        return pair(self.gateway.list(search=search, vtype=vtype, limit=limit, offset=offset), 'vouchers')

    def get(self, voucher_id: int) -> Optional[Dict]:
        self._require('voucher_view', context='voucher:get', payload={'id': voucher_id})
        voucher = self.gateway.get(voucher_id)
        return voucher if isinstance(voucher, dict) else None

    def _entity_type(self, voucher: Dict) -> str:
        vtype = (voucher or {}).get('type')
        if vtype == 'receipt':
            return 'RECEIPT_VOUCHER'
        if vtype == 'payment':
            return 'PAYMENT_VOUCHER'
        return 'EXPENSE_VOUCHER'

    def add(self, data: Dict):
        self._require('voucher_create', context='voucher:add', payload={'type': (data or {}).get('type')})
        if data.get('invoice_id'):
            try:
                from core.services.invoice_service import invoice_service
                inv = invoice_service.get(data.get('invoice_id'))
                if inv and inv.get('branch_id'):
                    data = dict(data)
                    data['branch_id'] = inv.get('branch_id')
            except Exception:
                pass
        data = branch_service.ensure_branch_id(data)
        data = cashbox_service.prepare_voucher_payload(data)
        voucher_id = self.gateway.create(data)
        cashbox_service.record_voucher(voucher_id, data)
        audit_service.log('CREATE', self._entity_type(data), voucher_id, new_values=data, details='إنشاء سند')
        return voucher_id

    def update(self, voucher_id: int, data: Dict):
        self._require('voucher_edit', context='voucher:update', payload={'id': voucher_id, 'type': (data or {}).get('type')})
        data = branch_service.ensure_branch_id(data)
        data = cashbox_service.prepare_voucher_payload(data)
        old = self.get(voucher_id)
        cashbox_service.reverse_voucher(voucher_id)
        result = self.gateway.update(voucher_id, data)
        cashbox_service.record_voucher(voucher_id, data)
        new = self.get(voucher_id)
        audit_service.log('UPDATE', self._entity_type(new or old or data), voucher_id, old_values=old, new_values=new or data, details='تعديل سند')
        return result

    def delete(self, voucher_id: int):
        self._require('voucher_delete', context='voucher:delete', payload={'id': voucher_id})
        old = self.get(voucher_id)
        cashbox_service.reverse_voucher(voucher_id)
        result = self.gateway.delete(voucher_id)
        audit_service.log('DELETE', self._entity_type(old or {}), voucher_id, old_values=old, details='حذف سند')
        return result

    def party_name(self, voucher: Dict) -> str:
        if voucher.get('customer_id'):
            customer = catalog_service.customer_by_id(voucher['customer_id'])
            return customer.get('name', '') if customer else ''
        if voucher.get('supplier_id'):
            supplier = catalog_service.supplier_by_id(voucher['supplier_id'])
            return supplier.get('name', '') if supplier else ''
        return ''


voucher_service = VoucherService()
