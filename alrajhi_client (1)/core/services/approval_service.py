# -*- coding: utf-8 -*-
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional
from auth.session import UserSession
from core.services.settings_service import settings_service
from core.services.audit_service import audit_service
from core.services.permission_service import permission_service
from core.services.rbac_service import rbac_service
from gateways.approval_gateway import create_approval_gateway

class ApprovalService:
    STATUS_PENDING = 'PENDING'; STATUS_APPROVED = 'APPROVED'; STATUS_REJECTED = 'REJECTED'; STATUS_CANCELLED = 'CANCELLED'
    def __init__(self, gateway=None):
        self.gateway = gateway or create_approval_gateway()
    def _decimal(self, value: Any) -> Decimal:
        try: return Decimal(str(value or '0'))
        except (InvalidOperation, ValueError): return Decimal('0')
    def _threshold(self, inv_type: str) -> Decimal:
        key = 'workflow/sales_approval_threshold' if inv_type == 'sale' else 'workflow/purchase_approval_threshold'
        return self._decimal(settings_service.get(key, '0'))
    def ensure_schema(self, conn=None) -> None:
        self.gateway.ensure_schema(conn)
    def requires_approval(self, invoice: Dict[str, Any]) -> bool:
        threshold = self._threshold((invoice or {}).get('type'))
        return threshold > 0 and self._decimal((invoice or {}).get('total')) >= threshold
    def ensure_invoice_request(self, invoice: Dict[str, Any], notes: str = '') -> Optional[int]:
        if not invoice or not invoice.get('id') or not self.requires_approval(invoice): return None
        username = UserSession.get_current_username() or UserSession.get_current_user_id() or ''
        request_id = self.gateway.ensure_invoice_request(invoice, self._threshold(invoice.get('type')), username, notes)
        if request_id is None:
            return None
        try:
            from core.services.advanced_approval_service import advanced_approval_service
            advanced_approval_service.ensure_steps_for_request(int(request_id), 'INVOICE', invoice.get('type'), invoice.get('total'))
        except Exception:
            pass
        audit_service.log('REQUEST_APPROVAL', 'INVOICE', invoice['id'], new_values={'approval_status':'PENDING'}, details=notes or 'طلب اعتماد فاتورة')
        return int(request_id)
    def assert_can_approve_invoice(self, invoice: Dict[str, Any]) -> None:
        if not invoice: raise ValueError('الفاتورة غير موجودة')
        role = (UserSession.get_current_user_role() or 'admin').lower()
        try:
            if rbac_service.list_roles():
                if not rbac_service.has_permission('approval.approve'):
                    permission_service.log_event('APPROVAL_DENIED', action='approval.approve', allowed=False, reason='rbac_permission_missing', context=str(invoice.get('id')))
                    raise PermissionError('لا تملك صلاحية اعتماد الفواتير حسب RBAC.')
                return
        except PermissionError:
            raise
        except Exception:
            pass
        if role != 'admin' and not settings_service.get_bool('approval/non_admin_can_approve', False):
            permission_service.log_event('APPROVAL_DENIED', action='approve_invoice', allowed=False, reason='approval_restricted_to_admin', context=str(invoice.get('id')))
            raise PermissionError('اعتماد الفواتير مسموح للمدير فقط حسب إعدادات الاعتماد.')
    def approve_invoice(self, invoice: Dict[str, Any], notes: str = '') -> None:
        self.assert_can_approve_invoice(invoice)
        if not self.requires_approval(invoice): return
        try:
            from core.services.advanced_approval_service import advanced_approval_service
            req_id = self.ensure_invoice_request(invoice, notes)
            if req_id:
                advanced_approval_service.ensure_steps_for_request(req_id, 'INVOICE', invoice.get('type'), invoice.get('total'))
                step = advanced_approval_service.pending_step(req_id)
                if step:
                    advanced_approval_service.approve_current_step(req_id, notes)
                    return
        except PermissionError:
            raise
        except Exception:
            pass
        self.ensure_invoice_request(invoice, notes)
        username = UserSession.get_current_username() or UserSession.get_current_user_id() or ''
        self.gateway.set_invoice_request_status(invoice['id'], self.STATUS_APPROVED, username, notes)
        audit_service.log('APPROVE', 'INVOICE_APPROVAL', invoice['id'], new_values={'approval_status':'APPROVED'}, details=notes or 'اعتماد فاتورة')
    def reject_invoice(self, invoice: Dict[str, Any], notes: str = '') -> None:
        if not invoice: raise ValueError('الفاتورة غير موجودة')
        try:
            if rbac_service.list_roles() and not rbac_service.has_permission('approval.reject'):
                permission_service.log_event('APPROVAL_DENIED', action='approval.reject', allowed=False, reason='rbac_permission_missing', context=str(invoice.get('id')))
                raise PermissionError('لا تملك صلاحية رفض الاعتماد حسب RBAC.')
        except PermissionError:
            raise
        except Exception:
            pass
        self.ensure_invoice_request(invoice, notes)
        username = UserSession.get_current_username() or UserSession.get_current_user_id() or ''
        self.gateway.set_invoice_request_status(invoice['id'], self.STATUS_REJECTED, username, notes)
        audit_service.log('REJECT', 'INVOICE_APPROVAL', invoice['id'], new_values={'approval_status':'REJECTED'}, details=notes or 'رفض فاتورة')
    def pending(self, limit: int = 200):
        return self.gateway.pending(limit)

approval_service = ApprovalService()
