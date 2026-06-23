# -*- coding: utf-8 -*-
"""Branch operation governance (Phase 202).

Branch master data affects warehouses, users, reports, and branch scoping.  UI
and service code must use one authorization/settings contract rather than
opening legacy dialogs directly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from core.services.audit_service import audit_service


@dataclass(frozen=True)
class BranchOperation:
    key: str
    setting_key: str
    permission_action: str
    label_key: str


class BranchOperationPolicy:
    OP_USE = 'use'
    OP_CREATE = 'create'
    OP_EDIT = 'edit'
    OP_ARCHIVE = 'archive'
    OP_SET_DEFAULT = 'set_default'

    def _permission_service(self):
        from core.services.permission_service import permission_service
        return permission_service

    def _settings_service(self):
        from core.services.settings_service import settings_service
        return settings_service

    def _operations(self) -> Dict[str, BranchOperation]:
        ps = self._permission_service()
        return {
            self.OP_USE: BranchOperation(self.OP_USE, 'allow_use', ps.ACTION_VIEW_ALL_BRANCHES, 'branches.operation.use'),
            self.OP_CREATE: BranchOperation(self.OP_CREATE, 'allow_create', ps.ACTION_MANAGE_ALL_BRANCHES, 'branches.operation.create'),
            self.OP_EDIT: BranchOperation(self.OP_EDIT, 'allow_edit', ps.ACTION_MANAGE_ALL_BRANCHES, 'branches.operation.edit'),
            self.OP_ARCHIVE: BranchOperation(self.OP_ARCHIVE, 'allow_archive', ps.ACTION_MANAGE_ALL_BRANCHES, 'branches.operation.archive'),
            self.OP_SET_DEFAULT: BranchOperation(self.OP_SET_DEFAULT, 'allow_set_default', ps.ACTION_MANAGE_ALL_BRANCHES, 'branches.operation.set_default'),
        }

    def settings(self) -> Dict[str, Any]:
        try:
            return self._settings_service().get_branch_settings()
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
        if operation_key == self.OP_USE:
            # Users may always open branch screens when the module is enabled;
            # row visibility remains governed by permission_service branch scope.
            return self.operation_allowed_by_settings(operation_key)
        return self.operation_allowed_by_settings(operation_key) and self._permission_service().can(op.permission_action)

    def denial_reason(self, operation_key: str) -> str:
        op = self._operations().get(operation_key)
        if not op:
            return 'unknown_branch_operation'
        if not self.is_enabled() and operation_key != self.OP_USE:
            return 'branches_disabled'
        if not self.operation_allowed_by_settings(operation_key):
            return f'branches_setting_{op.setting_key}_disabled'
        if operation_key != self.OP_USE and not self._permission_service().can(op.permission_action):
            return f'branches_permission_{op.permission_action}_missing'
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
                'BRANCH_OPERATION',
                None,
                new_values={'operation': operation_key, 'allowed': allowed, 'reason': reason, 'context': context, 'payload': payload or {}},
                details=f"branch_operation:{operation_key}:{'allowed' if allowed else 'denied'}",
            )
        except Exception:
            pass


branch_operation_policy = BranchOperationPolicy()
