# -*- coding: utf-8 -*-
"""Customer/supplier operation governance (Phase 207)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from core.services.audit_service import audit_service


@dataclass(frozen=True)
class PartyOperation:
    key: str
    setting_key: str
    permission_action: str
    label_key: str


class PartyOperationPolicy:
    OP_USE = 'use'
    OP_CUSTOMER_CREATE = 'customer_create'
    OP_CUSTOMER_EDIT = 'customer_edit'
    OP_CUSTOMER_DELETE = 'customer_delete'
    OP_CUSTOMER_VIEW = 'customer_view'
    OP_SUPPLIER_CREATE = 'supplier_create'
    OP_SUPPLIER_EDIT = 'supplier_edit'
    OP_SUPPLIER_DELETE = 'supplier_delete'
    OP_SUPPLIER_VIEW = 'supplier_view'

    def _permission_service(self):
        from core.services.permission_service import permission_service
        return permission_service

    def _settings_service(self):
        from core.services.settings_service import settings_service
        return settings_service

    def _operations(self) -> Dict[str, PartyOperation]:
        ps = self._permission_service()
        return {
            self.OP_USE: PartyOperation(self.OP_USE, 'allow_use', ps.ACTION_PARTY_VIEW, 'party.operation.use'),
            self.OP_CUSTOMER_VIEW: PartyOperation(self.OP_CUSTOMER_VIEW, 'allow_customer_view', ps.ACTION_CUSTOMER_VIEW, 'party.operation.customer_view'),
            self.OP_CUSTOMER_CREATE: PartyOperation(self.OP_CUSTOMER_CREATE, 'allow_customer_create', ps.ACTION_CUSTOMER_CREATE, 'party.operation.customer_create'),
            self.OP_CUSTOMER_EDIT: PartyOperation(self.OP_CUSTOMER_EDIT, 'allow_customer_edit', ps.ACTION_CUSTOMER_EDIT, 'party.operation.customer_edit'),
            self.OP_CUSTOMER_DELETE: PartyOperation(self.OP_CUSTOMER_DELETE, 'allow_customer_delete', ps.ACTION_CUSTOMER_DELETE, 'party.operation.customer_delete'),
            self.OP_SUPPLIER_VIEW: PartyOperation(self.OP_SUPPLIER_VIEW, 'allow_supplier_view', ps.ACTION_SUPPLIER_VIEW, 'party.operation.supplier_view'),
            self.OP_SUPPLIER_CREATE: PartyOperation(self.OP_SUPPLIER_CREATE, 'allow_supplier_create', ps.ACTION_SUPPLIER_CREATE, 'party.operation.supplier_create'),
            self.OP_SUPPLIER_EDIT: PartyOperation(self.OP_SUPPLIER_EDIT, 'allow_supplier_edit', ps.ACTION_SUPPLIER_EDIT, 'party.operation.supplier_edit'),
            self.OP_SUPPLIER_DELETE: PartyOperation(self.OP_SUPPLIER_DELETE, 'allow_supplier_delete', ps.ACTION_SUPPLIER_DELETE, 'party.operation.supplier_delete'),
        }

    def settings(self) -> Dict[str, Any]:
        try:
            return self._settings_service().get_party_settings()
        except Exception:
            return {'enabled': True, 'operations': {}}

    def is_enabled(self) -> bool:
        return bool(self.settings().get('enabled', True))

    def operation_allowed_by_settings(self, operation_key: str) -> bool:
        if not self.is_enabled() and operation_key != self.OP_USE:
            return False
        op = self._operations().get(operation_key)
        if not op:
            return True
        return bool((self.settings().get('operations', {}) or {}).get(op.setting_key, True))

    def can(self, operation_key: str) -> bool:
        op = self._operations().get(operation_key)
        if not op:
            return True
        return self.operation_allowed_by_settings(operation_key) and self._permission_service().can(op.permission_action)

    def denial_reason(self, operation_key: str) -> str:
        op = self._operations().get(operation_key)
        if not op:
            return 'unknown_party_operation'
        if not self.is_enabled() and operation_key != self.OP_USE:
            return 'parties_disabled'
        if not self.operation_allowed_by_settings(operation_key):
            return f'parties_setting_{op.setting_key}_disabled'
        if not self._permission_service().can(op.permission_action):
            return f'parties_permission_{op.permission_action}_missing'
        return ''

    def require(self, operation_key: str, context: str = '', payload: Dict[str, Any] | None = None) -> None:
        if self.can(operation_key):
            self.log(operation_key, True, context=context, payload=payload)
            return
        reason = self.denial_reason(operation_key)
        self.log(operation_key, False, reason=reason, context=context, payload=payload)
        raise PermissionError(reason)

    def log(self, operation_key: str, allowed: bool, reason: str = '', context: str = '', payload: Dict[str, Any] | None = None) -> None:
        try:
            audit_service.log(
                'SECURITY' if not allowed else 'CHECK',
                'PARTY_OPERATION',
                None,
                new_values={'operation': operation_key, 'allowed': allowed, 'reason': reason, 'context': context, 'payload': payload or {}},
                details=f"party_operation:{operation_key}:{'allowed' if allowed else 'denied'}",
            )
        except Exception:
            pass


party_operation_policy = PartyOperationPolicy()
