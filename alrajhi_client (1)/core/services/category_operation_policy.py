# -*- coding: utf-8 -*-
"""Category/catalog operation governance (Phase 205).

Categories are material master data.  They affect item classification, reports,
and item lookup filters; therefore UI and services must use one settings/RBAC
contract instead of inline dialogs or direct product-service calls.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from core.services.audit_service import audit_service


@dataclass(frozen=True)
class CategoryOperation:
    key: str
    setting_key: str
    permission_action: str
    label_key: str


class CategoryOperationPolicy:
    OP_USE = 'use'
    OP_CREATE = 'create'
    OP_EDIT = 'edit'
    OP_ARCHIVE = 'archive'
    OP_RESTORE = 'restore'

    def _permission_service(self):
        from core.services.permission_service import permission_service
        return permission_service

    def _settings_service(self):
        from core.services.settings_service import settings_service
        return settings_service

    def _operations(self) -> Dict[str, CategoryOperation]:
        ps = self._permission_service()
        return {
            self.OP_USE: CategoryOperation(self.OP_USE, 'allow_use', ps.ACTION_CATEGORY_VIEW, 'category.operation.use'),
            self.OP_CREATE: CategoryOperation(self.OP_CREATE, 'allow_create', ps.ACTION_CATEGORY_CREATE, 'category.operation.create'),
            self.OP_EDIT: CategoryOperation(self.OP_EDIT, 'allow_edit', ps.ACTION_CATEGORY_EDIT, 'category.operation.edit'),
            self.OP_ARCHIVE: CategoryOperation(self.OP_ARCHIVE, 'allow_archive', ps.ACTION_CATEGORY_ARCHIVE, 'category.operation.archive'),
            self.OP_RESTORE: CategoryOperation(self.OP_RESTORE, 'allow_restore', ps.ACTION_CATEGORY_RESTORE, 'category.operation.restore'),
        }

    def settings(self) -> Dict[str, Any]:
        try:
            return self._settings_service().get_category_settings()
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
            return 'unknown_category_operation'
        if not self.is_enabled() and operation_key != self.OP_USE:
            return 'categories_disabled'
        if not self.operation_allowed_by_settings(operation_key):
            return f'categories_setting_{op.setting_key}_disabled'
        if not self._permission_service().can(op.permission_action):
            return f'categories_permission_{op.permission_action}_missing'
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
                'CATEGORY_OPERATION',
                None,
                new_values={'operation': operation_key, 'allowed': allowed, 'reason': reason, 'context': context, 'payload': payload or {}},
                details=f"category_operation:{operation_key}:{'allowed' if allowed else 'denied'}",
            )
        except Exception:
            pass


category_operation_policy = CategoryOperationPolicy()
