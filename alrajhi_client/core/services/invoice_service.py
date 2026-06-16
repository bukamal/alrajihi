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
from core.services.workflow_policy_service import workflow_policy_service
from core.services.approval_service import approval_service
from core.services.accounting_service import accounting_service


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
        try:
            invoices = self.list_records()
        except Exception as exc:
            # Offline save path: duplicate reference pre-check is a convenience
            # only.  The queued server replay remains authoritative.
            print(f"⚠️ تعذر فحص تكرار مرجع الفاتورة؛ سيتم الاعتماد على الخادم عند المزامنة: {exc}")
            return False
        for inv in invoices:
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

    def _client_side_movements_enabled(self) -> bool:
        """Return True only when the client is the authoritative local store.

        In remote/client mode the server invoice endpoint already creates and
        reverses invoice stock movements inside the same transaction.  Repeating
        those calls from the desktop caused duplicate remote stock effects and,
        while offline, crashes because warehouse movement endpoints are not
        safely queueable independently from their parent invoice.
        """
        try:
            return not bool(self.gateway.is_remote())
        except Exception:
            return True

    def create(self, data: Dict) -> int:
        workflow_policy_service.ensure_schema()
        data = dict(data or {})
        if not data.get('workflow_status'):
            data['workflow_status'] = workflow_policy_service.initial_status(data.get('type'), data.get('total'))
        if data.get('workflow_status') == workflow_policy_service.SUBMITTED and not data.get('submitted_at'):
            from datetime import datetime
            data['submitted_at'] = datetime.now().isoformat(timespec='seconds')
        data = branch_service.ensure_branch_id(data)
        invoice_id = self.gateway.create(data)
        # Phase154: create the approval request immediately for threshold-driven submitted documents.
        # Phase152 only marked the invoice as SUBMITTED; this closes the workflow gap so
        # pending approvals appear without requiring a second manual submit call.
        try:
            if data.get('workflow_status') == workflow_policy_service.SUBMITTED:
                approval_payload = dict(data)
                approval_payload['id'] = invoice_id
                approval_service.ensure_invoice_request(approval_payload, 'طلب اعتماد تلقائي بسبب تجاوز حد الاعتماد')
        except Exception as exc:
            # Do not lose the invoice if approval logging fails; surface through audit/diagnostics later.
            audit_service.log('APPROVAL_AUTO_REQUEST_FAILED', 'INVOICE', invoice_id, new_values={'error': str(exc)}, details='تعذر إنشاء طلب الاعتماد التلقائي')
        if self._client_side_movements_enabled():
            warehouse_service.record_invoice_movements(invoice_id, data)
        audit_service.log('CREATE', 'SALE_INVOICE' if data.get('type') == 'sale' else 'PURCHASE_INVOICE', invoice_id, new_values=data, details='إنشاء فاتورة')
        return invoice_id

    def update(self, invoice_id: int, data: Dict):
        workflow_policy_service.ensure_schema()
        data = branch_service.ensure_branch_id(data)
        old = self.get(invoice_id)
        workflow_policy_service.assert_can_edit(old, 'INVOICE')
        if self.has_linked_returns(invoice_id):
            raise ValueError('لا يمكن تعديل فاتورة مرتبطة بمرتجعات. ألغِ المرتجعات أولاً.')
        if self._client_side_movements_enabled():
            warehouse_service.reverse_invoice_movements(invoice_id, old)
        result = self.gateway.update(invoice_id, data)
        if self._client_side_movements_enabled():
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

    def has_linked_returns(self, invoice_id: int) -> bool:
        try:
            return bool(self.gateway.has_linked_returns(invoice_id))
        except Exception:
            return False

    def delete(self, invoice_id: int):
        workflow_policy_service.ensure_schema()
        old = self.get(invoice_id)
        workflow_policy_service.assert_can_delete(old, 'INVOICE')
        if self.has_linked_returns(invoice_id):
            raise ValueError('لا يمكن حذف فاتورة مرتبطة بمرتجعات. ألغِ المرتجعات أولاً.')
        if self._client_side_movements_enabled():
            warehouse_service.reverse_invoice_movements(invoice_id, old)
        result = self.gateway.delete(invoice_id)
        entity = 'SALE_INVOICE' if (old or {}).get('type') == 'sale' else 'PURCHASE_INVOICE'
        audit_service.log('SOFT_DELETE', entity, invoice_id, old_values=old, details='إلغاء/حذف فاتورة')
        return result

    def submit(self, invoice_id: int, notes: str = '') -> str:
        invoice = self.get(invoice_id)
        if invoice:
            approval_service.ensure_invoice_request(invoice, notes or 'إرسال الفاتورة للاعتماد')
        return workflow_policy_service.transition_invoice(invoice_id, workflow_policy_service.SUBMITTED, 'submit', notes or 'إرسال الفاتورة للاعتماد')

    def approve(self, invoice_id: int, notes: str = '') -> str:
        invoice = self.get(invoice_id)
        approval_service.approve_invoice(invoice, notes or 'اعتماد الفاتورة')
        return workflow_policy_service.transition_invoice(invoice_id, workflow_policy_service.APPROVED, 'approve', notes or 'اعتماد الفاتورة')

    def reject(self, invoice_id: int, notes: str = '') -> str:
        invoice = self.get(invoice_id)
        approval_service.reject_invoice(invoice, notes or 'رفض الفاتورة')
        return workflow_policy_service.transition_invoice(invoice_id, workflow_policy_service.CANCELLED, 'reject', notes or 'رفض الفاتورة')

    def post(self, invoice_id: int, notes: str = '') -> str:
        invoice = self.get(invoice_id)
        status = (invoice or {}).get('workflow_status', 'DRAFT')
        if status != workflow_policy_service.APPROVED:
            raise ValueError('لا يمكن ترحيل الفاتورة محاسبيًا قبل اعتمادها.')
        new_status = workflow_policy_service.transition_invoice(invoice_id, workflow_policy_service.POSTED, 'post', notes or 'ترحيل الفاتورة')
        accounting_service.post_invoice(self.get(invoice_id) or invoice, notes or 'قيد تلقائي من ترحيل فاتورة')
        return new_status

    def cancel(self, invoice_id: int, notes: str = '') -> str:
        return workflow_policy_service.transition_invoice(invoice_id, workflow_policy_service.CANCELLED, 'cancel', notes or 'إلغاء الفاتورة')

    def reopen(self, invoice_id: int, notes: str = '') -> str:
        return workflow_policy_service.transition_invoice(invoice_id, workflow_policy_service.DRAFT, 'reopen', notes or 'إعادة فتح الفاتورة')

    def next_reference(self, inv_type: str) -> str:
        try:
            return self.gateway.next_reference(inv_type)
        except Exception as exc:
            # Remote offline fallback.  The reference must be stable enough for
            # the local queued payload, while the server can still validate it
            # when replaying the queue.
            from datetime import datetime
            prefix = 'SOFF' if inv_type == 'sale' else 'POFF'
            ref = f"{prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            print(f"⚠️ تعذر جلب رقم الفاتورة من الخادم؛ تم توليد رقم مؤقت {ref}: {exc}")
            return ref


invoice_service = InvoiceService()
