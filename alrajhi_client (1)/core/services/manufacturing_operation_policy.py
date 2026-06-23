# -*- coding: utf-8 -*-
"""Manufacturing operation governance.

Phase 187 centralizes manufacturing permissions, operation switches, and audit
logging. Manufacturing UI and services should call this policy instead of
reading settings, RBAC, or legacy role fields directly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

from core.services.audit_service import audit_service
from core.services.permission_service import permission_service
from core.services.settings_service import settings_service


@dataclass(frozen=True)
class ManufacturingOperation:
    key: str
    setting_key: str
    permission_action: str
    label_key: str


class ManufacturingOperationPolicy:
    OP_USE = 'use'
    OP_BOM_CREATE = 'bom_create'
    OP_BOM_EDIT = 'bom_edit'
    OP_BOM_DELETE = 'bom_delete'
    OP_ORDER_CREATE = 'order_create'
    OP_ORDER_START = 'order_start'
    OP_MATERIAL_CONSUME = 'material_consume'
    OP_OUTPUT_COMPLETE = 'output_complete'
    OP_ORDER_CANCEL = 'order_cancel'
    OP_ORDER_DELETE = 'order_delete'
    OP_ORDER_REVERSE = 'order_reverse'
    OP_CONSUMPTION_DELETE = 'consumption_delete'
    OP_OUTPUT_DELETE = 'output_delete'
    OP_COST_VIEW = 'cost_view'
    OP_PRINT = 'print'

    OPERATIONS: Dict[str, ManufacturingOperation] = {
        OP_USE: ManufacturingOperation(OP_USE, 'allow_use', permission_service.ACTION_USE_MANUFACTURING, 'manufacturing.operation.use'),
        OP_BOM_CREATE: ManufacturingOperation(OP_BOM_CREATE, 'allow_bom_create', permission_service.ACTION_MANUFACTURING_BOM_CREATE, 'manufacturing.operation.bom_create'),
        OP_BOM_EDIT: ManufacturingOperation(OP_BOM_EDIT, 'allow_bom_edit', permission_service.ACTION_MANUFACTURING_BOM_EDIT, 'manufacturing.operation.bom_edit'),
        OP_BOM_DELETE: ManufacturingOperation(OP_BOM_DELETE, 'allow_bom_delete', permission_service.ACTION_MANUFACTURING_BOM_DELETE, 'manufacturing.operation.bom_delete'),
        OP_ORDER_CREATE: ManufacturingOperation(OP_ORDER_CREATE, 'allow_order_create', permission_service.ACTION_MANUFACTURING_ORDER_CREATE, 'manufacturing.operation.order_create'),
        OP_ORDER_START: ManufacturingOperation(OP_ORDER_START, 'allow_order_start', permission_service.ACTION_MANUFACTURING_ORDER_START, 'manufacturing.operation.order_start'),
        OP_MATERIAL_CONSUME: ManufacturingOperation(OP_MATERIAL_CONSUME, 'allow_material_consume', permission_service.ACTION_MANUFACTURING_MATERIAL_CONSUME, 'manufacturing.operation.material_consume'),
        OP_OUTPUT_COMPLETE: ManufacturingOperation(OP_OUTPUT_COMPLETE, 'allow_output_complete', permission_service.ACTION_MANUFACTURING_OUTPUT_COMPLETE, 'manufacturing.operation.output_complete'),
        OP_ORDER_CANCEL: ManufacturingOperation(OP_ORDER_CANCEL, 'allow_order_cancel', permission_service.ACTION_MANUFACTURING_ORDER_CANCEL, 'manufacturing.operation.order_cancel'),
        OP_ORDER_DELETE: ManufacturingOperation(OP_ORDER_DELETE, 'allow_order_delete', permission_service.ACTION_MANUFACTURING_ORDER_DELETE, 'manufacturing.operation.order_delete'),
        OP_ORDER_REVERSE: ManufacturingOperation(OP_ORDER_REVERSE, 'allow_order_reverse', permission_service.ACTION_MANUFACTURING_ORDER_REVERSE, 'manufacturing.operation.order_reverse'),
        OP_CONSUMPTION_DELETE: ManufacturingOperation(OP_CONSUMPTION_DELETE, 'allow_consumption_delete', permission_service.ACTION_MANUFACTURING_CONSUMPTION_DELETE, 'manufacturing.operation.consumption_delete'),
        OP_OUTPUT_DELETE: ManufacturingOperation(OP_OUTPUT_DELETE, 'allow_output_delete', permission_service.ACTION_MANUFACTURING_OUTPUT_DELETE, 'manufacturing.operation.output_delete'),
        OP_COST_VIEW: ManufacturingOperation(OP_COST_VIEW, 'allow_cost_view', permission_service.ACTION_MANUFACTURING_COST_VIEW, 'manufacturing.operation.cost_view'),
        OP_PRINT: ManufacturingOperation(OP_PRINT, 'allow_print', permission_service.ACTION_MANUFACTURING_PRINT, 'manufacturing.operation.print'),
    }

    def settings(self) -> Dict[str, Any]:
        return settings_service.get_manufacturing_settings()

    def is_enabled(self) -> bool:
        return bool(self.settings().get('enabled', True))

    def operation_allowed_by_settings(self, operation_key: str) -> bool:
        if not self.is_enabled() and operation_key != self.OP_USE:
            return False
        op = self.OPERATIONS.get(operation_key)
        if not op:
            return True
        operations = self.settings().get('operations', {}) or {}
        if op.setting_key == 'allow_cost_view':
            # Cost visibility is primarily a permission/security policy. No
            # dedicated operation switch is required unless added later.
            return True
        return bool(operations.get(op.setting_key, True))

    def can(self, operation_key: str) -> bool:
        op = self.OPERATIONS.get(operation_key)
        if not op:
            return True
        return self.operation_allowed_by_settings(operation_key) and permission_service.can(op.permission_action)

    def denial_reason(self, operation_key: str) -> str:
        op = self.OPERATIONS.get(operation_key)
        if not op:
            return 'unknown_manufacturing_operation'
        if not self.is_enabled() and operation_key != self.OP_USE:
            return 'manufacturing_disabled'
        if not self.operation_allowed_by_settings(operation_key):
            return f'manufacturing_setting_{op.setting_key}_disabled'
        if not permission_service.can(op.permission_action):
            return f'manufacturing_permission_{op.permission_action}_missing'
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
                'MANUFACTURING_OPERATION',
                None,
                new_values={'operation': operation_key, 'allowed': allowed, 'reason': reason, 'context': context, 'payload': payload or {}},
                details=f"manufacturing_operation:{operation_key}:{'allowed' if allowed else 'denied'}",
            )
        except Exception:
            pass


manufacturing_operation_policy = ManufacturingOperationPolicy()
