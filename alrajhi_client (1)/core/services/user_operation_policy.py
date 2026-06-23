# -*- coding: utf-8 -*-
"""User-management operation governance (Phase 206).

User master data controls access to the whole ERP.  UI and services must use a
single settings/RBAC contract instead of opening legacy QDialogs directly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from core.services.audit_service import audit_service


@dataclass(frozen=True)
class UserOperation:
    key: str
    setting_key: str
    permission_action: str
    label_key: str


class UserOperationPolicy:
    OP_USE = 'use'
    OP_CREATE = 'create'
    OP_EDIT = 'edit'
    OP_DELETE = 'delete'
    OP_CHANGE_PASSWORD = 'change_password'

    def _permission_service(self):
        from core.services.permission_service import permission_service
        return permission_service

    def _settings_service(self):
        from core.services.settings_service import settings_service
        return settings_service

    def _operations(self) -> Dict[str, UserOperation]:
        ps = self._permission_service()
        return {
            self.OP_USE: UserOperation(self.OP_USE, 'allow_use', ps.ACTION_USERS_MANAGE, 'users.operation.use'),
            self.OP_CREATE: UserOperation(self.OP_CREATE, 'allow_create', ps.ACTION_USERS_MANAGE, 'users.operation.create'),
            self.OP_EDIT: UserOperation(self.OP_EDIT, 'allow_edit', ps.ACTION_USERS_MANAGE, 'users.operation.edit'),
            self.OP_DELETE: UserOperation(self.OP_DELETE, 'allow_delete', ps.ACTION_USERS_MANAGE, 'users.operation.delete'),
            self.OP_CHANGE_PASSWORD: UserOperation(self.OP_CHANGE_PASSWORD, 'allow_change_password', ps.ACTION_USERS_MANAGE, 'users.operation.change_password'),
        }

    def settings(self) -> Dict[str, Any]:
        try:
            return self._settings_service().get_user_settings()
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
        operations = self.settings().get('operations', {}) or {}
        return bool(operations.get(op.setting_key, True))

    def can(self, operation_key: str) -> bool:
        op = self._operations().get(operation_key)
        if not op:
            return True
        return self.operation_allowed_by_settings(operation_key) and self._permission_service().can(op.permission_action)

    def denial_reason(self, operation_key: str) -> str:
        op = self._operations().get(operation_key)
        if not op:
            return 'unknown_user_operation'
        if not self.is_enabled() and operation_key != self.OP_USE:
            return 'users_disabled'
        if not self.operation_allowed_by_settings(operation_key):
            return f'users_setting_{op.setting_key}_disabled'
        if not self._permission_service().can(op.permission_action):
            return f'users_permission_{op.permission_action}_missing'
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
                'USER_OPERATION',
                None,
                new_values={'operation': operation_key, 'allowed': allowed, 'reason': reason, 'context': context, 'payload': payload or {}},
                details=f"user_operation:{operation_key}:{'allowed' if allowed else 'denied'}",
            )
        except Exception:
            pass


user_operation_policy = UserOperationPolicy()
