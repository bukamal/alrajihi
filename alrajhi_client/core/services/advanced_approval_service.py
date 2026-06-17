# -*- coding: utf-8 -*-
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from auth.session import UserSession
from core.services.rbac_service import rbac_service
from core.services.audit_service import audit_service
from core.services.permission_service import permission_service
from gateways.approval_gateway import create_approval_gateway


class AdvancedApprovalService:
    """Multi-level approval engine.

    The service owns business authorization and audit orchestration.  Persistence
    is delegated to ApprovalGateway so protected service layers no longer touch
    DatabaseConnection/SQL directly.
    """

    def __init__(self, gateway=None):
        self.gateway = gateway or create_approval_gateway()

    def _decimal(self, value: Any) -> Decimal:
        try:
            return Decimal(str(value or '0'))
        except (InvalidOperation, ValueError):
            return Decimal('0')

    def ensure_schema(self, conn=None) -> None:
        self.gateway.ensure_advanced_schema(conn)

    def matrix_for(self, document_type: str, invoice_type: str | None, amount: Any) -> List[Dict[str, Any]]:
        return self.gateway.matrix_for(document_type, invoice_type, amount)

    def ensure_steps_for_request(self, approval_request_id: int, document_type: str='INVOICE', invoice_type: str | None=None, amount: Any=0) -> int:
        return self.gateway.ensure_steps_for_request(approval_request_id, document_type, invoice_type, amount)

    def ensure_invoice_steps(self, invoice: Dict[str, Any]) -> int:
        if not invoice or not invoice.get('id'):
            return 0
        from core.services.approval_service import approval_service
        request_id = approval_service.ensure_invoice_request(invoice, 'multi-level approval')
        if not request_id:
            return 0
        return self.ensure_steps_for_request(request_id, 'INVOICE', invoice.get('type'), invoice.get('total'))

    def pending_step(self, approval_request_id: int) -> Optional[Dict[str, Any]]:
        return self.gateway.pending_step(approval_request_id)

    def approve_current_step(self, approval_request_id: int, notes: str='') -> Dict[str, Any]:
        step = self.pending_step(approval_request_id)
        if not step:
            return {'status': 'already_complete'}
        perm = step.get('required_permission') or 'approval.approve'
        role = (step.get('required_role') or '').lower()
        user_roles = [r.lower() for r in rbac_service.effective_user_roles()]
        if role and role not in user_roles and 'admin' not in user_roles:
            permission_service.log_event('APPROVAL_DENIED', action=perm, allowed=False, reason='required_role_missing', context=str(approval_request_id))
            raise PermissionError(f'تتطلب هذه الخطوة دور: {role}')
        if not rbac_service.has_permission(perm):
            permission_service.log_event('APPROVAL_DENIED', action=perm, allowed=False, reason='permission_missing', context=str(approval_request_id))
            raise PermissionError(f'تتطلب هذه الخطوة صلاحية: {perm}')
        username = UserSession.get_current_username() or UserSession.get_current_user_id() or ''
        result = self.gateway.approve_current_step(approval_request_id, username, notes)
        audit_service.log(
            'APPROVE_STEP',
            'APPROVAL_REQUEST',
            approval_request_id,
            new_values={'step': result.get('step_order') or step.get('step_order'), 'remaining': int(result.get('remaining_steps') or 0)},
            details=notes,
        )
        return result

    def request_status(self, approval_request_id: int) -> Dict[str, Any]:
        return self.gateway.request_status(approval_request_id)


advanced_approval_service = AdvancedApprovalService()
