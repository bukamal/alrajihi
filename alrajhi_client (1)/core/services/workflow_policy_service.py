# -*- coding: utf-8 -*-
"""Workflow policy service (Phase 151).

Centralizes document lifecycle rules for invoices and other future business
objects. The first integration point is invoices because they carry inventory,
financial and return-side effects.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional

from core.services.settings_service import settings_service
from core.services.audit_service import audit_service
from core.services.permission_service import permission_service
from gateways.workflow_gateway import create_workflow_gateway


class WorkflowPolicyService:
    DRAFT = 'DRAFT'
    SUBMITTED = 'SUBMITTED'
    APPROVED = 'APPROVED'
    POSTED = 'POSTED'
    CANCELLED = 'CANCELLED'

    VALID_STATUSES = {DRAFT, SUBMITTED, APPROVED, POSTED, CANCELLED}

    ACTION_SUBMIT = 'workflow.submit'
    ACTION_APPROVE = 'workflow.approve'
    ACTION_POST = 'workflow.post'
    ACTION_CANCEL = 'workflow.cancel'
    ACTION_REOPEN = 'workflow.reopen'

    DEFAULT_EDIT_POLICY = {
        DRAFT: True,
        SUBMITTED: True,
        APPROVED: False,
        POSTED: False,
        CANCELLED: False,
    }
    DEFAULT_DELETE_POLICY = {
        DRAFT: True,
        SUBMITTED: True,
        APPROVED: False,
        POSTED: False,
        CANCELLED: False,
    }

    def normalize_status(self, status: Any) -> str:
        value = str(status or self.DRAFT).strip().upper()
        return value if value in self.VALID_STATUSES else self.DRAFT

    def _setting_bool(self, key: str, default: bool) -> bool:
        try:
            return settings_service.get_bool(key, default)
        except Exception:
            return default

    def _to_decimal(self, value: Any) -> Decimal:
        try:
            return Decimal(str(value or '0'))
        except (InvalidOperation, ValueError):
            return Decimal('0')

    def workflow_enabled(self) -> bool:
        return self._setting_bool('workflow/enabled', False)

    def approval_required(self) -> bool:
        return self._setting_bool('workflow/approval_required', False)

    def threshold_for(self, doc_type: str) -> Decimal:
        key = 'workflow/sales_approval_threshold' if doc_type == 'sale' else 'workflow/purchase_approval_threshold'
        return self._to_decimal(settings_service.get(key, '0'))

    def initial_status(self, doc_type: str, total: Any) -> str:
        """Return initial lifecycle status for a new document.

        A positive approval threshold marks large documents as SUBMITTED so they
        can be discovered by diagnostics/approval screens. Otherwise documents
        remain DRAFT to preserve current editable workflows until explicit
        approval/posting UI is introduced.
        """
        if not self.workflow_enabled() or not self.approval_required():
            return self.DRAFT
        amount = self._to_decimal(total)
        threshold = self.threshold_for(doc_type)
        if threshold > 0 and amount >= threshold:
            return self.SUBMITTED
        return self.DRAFT

    def can_edit_status(self, status: Any) -> bool:
        status = self.normalize_status(status)
        key = f'workflow/allow_edit_{status.lower()}'
        return self._setting_bool(key, self.DEFAULT_EDIT_POLICY.get(status, False))

    def can_delete_status(self, status: Any) -> bool:
        status = self.normalize_status(status)
        key = f'workflow/allow_delete_{status.lower()}'
        return self._setting_bool(key, self.DEFAULT_DELETE_POLICY.get(status, False))

    def assert_can_edit(self, document: Optional[Dict], entity_type: str = 'INVOICE') -> None:
        status = self.normalize_status((document or {}).get('workflow_status') or (document or {}).get('status'))
        if not self.workflow_enabled():
            return
        if not permission_service.can(permission_service.ACTION_EDIT_INVOICES):
            raise PermissionError(permission_service.denied_message(permission_service.ACTION_EDIT_INVOICES))
        if not self.can_edit_status(status):
            permission_service.log_event('WORKFLOW_DENIED', action='edit', allowed=False,
                                         reason=f'edit_not_allowed_for_{status.lower()}', context=entity_type)
            raise ValueError(f'لا يمكن تعديل المستند في حالة {status}. غيّر سياسة سير العمل أو أعد فتح المستند.')

    def assert_can_delete(self, document: Optional[Dict], entity_type: str = 'INVOICE') -> None:
        status = self.normalize_status((document or {}).get('workflow_status') or (document or {}).get('status'))
        if not self.workflow_enabled():
            return
        if not permission_service.can(permission_service.ACTION_DELETE):
            raise PermissionError(permission_service.denied_message(permission_service.ACTION_DELETE))
        if not self.can_delete_status(status):
            permission_service.log_event('WORKFLOW_DENIED', action='delete', allowed=False,
                                         reason=f'delete_not_allowed_for_{status.lower()}', context=entity_type)
            raise ValueError(f'لا يمكن حذف المستند في حالة {status}. استخدم الإلغاء أو أعد فتح المستند حسب السياسة.')

    def _gateway(self):
        return create_workflow_gateway()

    def ensure_schema(self) -> None:
        try:
            self._gateway().ensure_schema()
        except Exception:
            pass

    def transition_invoice(self, invoice_id: int, new_status: str, action: str, notes: str = '') -> str:
        old_status = None
        result = self._gateway().transition_invoice(invoice_id, new_status, action, notes)
        audit_service.log(action.upper(), 'INVOICE_WORKFLOW', invoice_id,
                          old_values={'workflow_status': old_status} if old_status else {},
                          new_values={'workflow_status': result}, details=notes or action)
        return self.normalize_status(result)

    def diagnostics(self) -> Dict[str, Any]:
        try:
            return self._gateway().diagnostics()
        except Exception as exc:
            return {'mode': 'error', 'error': str(exc)}


workflow_policy_service = WorkflowPolicyService()
