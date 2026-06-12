# -*- coding: utf-8 -*-
"""Invoice application service.

This facade keeps invoice widgets/dialogs away from legacy DAO return-shape
variance while preserving the existing invoice DAO and repository behavior.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from core.compat import records, pair
from gateways.invoice_gateway import create_invoice_gateway
from core.services.audit_service import audit_service
from core.services.warehouse_service import warehouse_service
from core.services.branch_service import branch_service


class InvoiceService:
    def __init__(self, gateway=None):
        self.gateway = gateway or create_invoice_gateway()

    def list_invoices(self, search: str | None = None, inv_type: str | None = None,
                      start_date: str | None = None, end_date: str | None = None,
                      customer_id: int | None = None, supplier_id: int | None = None,
                      limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict], int]:
        return pair(self.gateway.list(
            search=search, inv_type=inv_type, start_date=start_date, end_date=end_date,
            customer_id=customer_id, supplier_id=supplier_id, limit=limit, offset=offset
        ), 'invoices')


    def list_records(self, search: str | None = None, inv_type: str | None = None,
                     start_date: str | None = None, end_date: str | None = None,
                     customer_id: int | None = None, supplier_id: int | None = None,
                     limit: int | None = None, offset: int | None = None) -> List[Dict]:
        invoices, _ = self.list_invoices(
            search=search, inv_type=inv_type, start_date=start_date, end_date=end_date,
            customer_id=customer_id, supplier_id=supplier_id, limit=limit, offset=offset
        )
        return invoices

    def unpaid_invoices(self, inv_type: str | None, customer_id: int | None = None,
                        supplier_id: int | None = None, limit: int = 100) -> List[Dict]:
        invoices = self.list_records(
            inv_type=inv_type, customer_id=customer_id, supplier_id=supplier_id,
            limit=limit, offset=0
        )
        result = []
        for inv in invoices:
            try:
                remaining = float(inv.get('total', 0) or 0) - float(inv.get('paid', 0) or 0)
            except Exception:
                remaining = 0
            if remaining > 0:
                result.append(inv)
        return result

    def reference_exists(self, reference: str, exclude_invoice_id: int | None = None) -> bool:
        if not reference:
            return False
        for inv in self.list_records():
            if exclude_invoice_id is not None and inv.get('id') == exclude_invoice_id:
                continue
            if inv.get('reference') == reference:
                return True
        return False

    def pending_count(self) -> int:
        return len(self.unpaid_invoices(inv_type=None, limit=1000000))

    def get(self, invoice_id: int) -> Optional[Dict]:
        invoice = self.gateway.get(invoice_id)
        return invoice if isinstance(invoice, dict) else None

    def create(self, data: Dict) -> int:
        data = branch_service.ensure_branch_id(data)
        invoice_id = self.gateway.create(data)
        warehouse_service.record_invoice_movements(invoice_id, data)
        audit_service.log('CREATE', 'SALE_INVOICE' if data.get('type') == 'sale' else 'PURCHASE_INVOICE', invoice_id, new_values=data, details='إنشاء فاتورة')
        return invoice_id

    def update(self, invoice_id: int, data: Dict):
        data = branch_service.ensure_branch_id(data)
        old = self.get(invoice_id)
        warehouse_service.reverse_invoice_movements(invoice_id)
        result = self.gateway.update(invoice_id, data)
        warehouse_service.record_invoice_movements(invoice_id, data)
        new = self.get(invoice_id)
        entity = 'SALE_INVOICE' if (old or data).get('type') == 'sale' else 'PURCHASE_INVOICE'
        audit_service.log('UPDATE', entity, invoice_id, old_values=old, new_values=new or data, details='تعديل فاتورة')
        return result

    def has_linked_vouchers(self, invoice_id: int) -> bool:
        try:
            return bool(self.gateway.has_linked_vouchers(invoice_id))
        except Exception:
            return False

    def delete(self, invoice_id: int):
        old = self.get(invoice_id)
        warehouse_service.reverse_invoice_movements(invoice_id)
        result = self.gateway.delete(invoice_id)
        entity = 'SALE_INVOICE' if (old or {}).get('type') == 'sale' else 'PURCHASE_INVOICE'
        audit_service.log('SOFT_DELETE', entity, invoice_id, old_values=old, details='إلغاء/حذف فاتورة')
        return result

    def next_reference(self, inv_type: str) -> str:
        return self.gateway.next_reference(inv_type)


invoice_service = InvoiceService()
