# -*- coding: utf-8 -*-
"""Inventory / warehouse operation governance (Phase 194).

Warehouse master data, stock movements, transfers, and ledger tools are shared
by invoices, returns, POS, restaurant, and manufacturing.  UI and service code
should not make separate authorization decisions; this policy routes checks
through settings_service, permission_service, and audit_service.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from core.services.audit_service import audit_service
from core.services.permission_service import permission_service
from core.services.settings_service import settings_service


@dataclass(frozen=True)
class InventoryOperation:
    key: str
    setting_key: str
    permission_action: str
    label_key: str


class InventoryOperationPolicy:
    OP_USE = 'use'
    OP_WAREHOUSE_CREATE = 'warehouse_create'
    OP_WAREHOUSE_EDIT = 'warehouse_edit'
    OP_WAREHOUSE_ARCHIVE = 'warehouse_archive'
    OP_BALANCE_VIEW = 'balance_view'
    OP_MOVEMENT_VIEW = 'movement_view'
    OP_DIRECT_MOVEMENT = 'direct_movement'
    OP_TRANSFER_CREATE = 'transfer_create'
    OP_TRANSFER_CANCEL = 'transfer_cancel'
    OP_LEDGER_VIEW = 'ledger_view'
    OP_LEDGER_BACKFILL = 'ledger_backfill'
    OP_RECONCILE = 'reconcile'
    OP_PRINT = 'print'

    OPERATIONS: Dict[str, InventoryOperation] = {
        OP_USE: InventoryOperation(OP_USE, 'allow_use', permission_service.ACTION_USE_INVENTORY, 'inventory.operation.use'),
        OP_WAREHOUSE_CREATE: InventoryOperation(OP_WAREHOUSE_CREATE, 'allow_warehouse_create', permission_service.ACTION_INVENTORY_WAREHOUSE_CREATE, 'inventory.operation.warehouse_create'),
        OP_WAREHOUSE_EDIT: InventoryOperation(OP_WAREHOUSE_EDIT, 'allow_warehouse_edit', permission_service.ACTION_INVENTORY_WAREHOUSE_EDIT, 'inventory.operation.warehouse_edit'),
        OP_WAREHOUSE_ARCHIVE: InventoryOperation(OP_WAREHOUSE_ARCHIVE, 'allow_warehouse_archive', permission_service.ACTION_INVENTORY_WAREHOUSE_ARCHIVE, 'inventory.operation.warehouse_archive'),
        OP_BALANCE_VIEW: InventoryOperation(OP_BALANCE_VIEW, 'allow_balance_view', permission_service.ACTION_INVENTORY_BALANCE_VIEW, 'inventory.operation.balance_view'),
        OP_MOVEMENT_VIEW: InventoryOperation(OP_MOVEMENT_VIEW, 'allow_movement_view', permission_service.ACTION_INVENTORY_MOVEMENT_VIEW, 'inventory.operation.movement_view'),
        OP_DIRECT_MOVEMENT: InventoryOperation(OP_DIRECT_MOVEMENT, 'allow_direct_movement', permission_service.ACTION_INVENTORY_DIRECT_MOVEMENT, 'inventory.operation.direct_movement'),
        OP_TRANSFER_CREATE: InventoryOperation(OP_TRANSFER_CREATE, 'allow_transfer_create', permission_service.ACTION_INVENTORY_TRANSFER_CREATE, 'inventory.operation.transfer_create'),
        OP_TRANSFER_CANCEL: InventoryOperation(OP_TRANSFER_CANCEL, 'allow_transfer_cancel', permission_service.ACTION_INVENTORY_TRANSFER_CANCEL, 'inventory.operation.transfer_cancel'),
        OP_LEDGER_VIEW: InventoryOperation(OP_LEDGER_VIEW, 'allow_ledger_view', permission_service.ACTION_INVENTORY_LEDGER_VIEW, 'inventory.operation.ledger_view'),
        OP_LEDGER_BACKFILL: InventoryOperation(OP_LEDGER_BACKFILL, 'allow_ledger_backfill', permission_service.ACTION_INVENTORY_LEDGER_BACKFILL, 'inventory.operation.ledger_backfill'),
        OP_RECONCILE: InventoryOperation(OP_RECONCILE, 'allow_reconcile', permission_service.ACTION_INVENTORY_RECONCILE, 'inventory.operation.reconcile'),
        OP_PRINT: InventoryOperation(OP_PRINT, 'allow_print', permission_service.ACTION_INVENTORY_PRINT, 'inventory.operation.print'),
    }

    def settings(self) -> Dict[str, Any]:
        try:
            return settings_service.get_inventory_settings()
        except Exception:
            return {'enabled': True, 'operations': {}}

    def is_enabled(self) -> bool:
        return bool(self.settings().get('enabled', True))

    def operation_allowed_by_settings(self, operation_key: str) -> bool:
        if not self.is_enabled() and operation_key != self.OP_USE:
            return False
        op = self.OPERATIONS.get(operation_key)
        if not op:
            return True
        operations = self.settings().get('operations', {}) or {}
        return bool(operations.get(op.setting_key, True))

    def can(self, operation_key: str) -> bool:
        op = self.OPERATIONS.get(operation_key)
        if not op:
            return True
        return self.operation_allowed_by_settings(operation_key) and permission_service.can(op.permission_action)

    def denial_reason(self, operation_key: str) -> str:
        op = self.OPERATIONS.get(operation_key)
        if not op:
            return 'unknown_inventory_operation'
        if not self.is_enabled() and operation_key != self.OP_USE:
            return 'inventory_disabled'
        if not self.operation_allowed_by_settings(operation_key):
            return f'inventory_setting_{op.setting_key}_disabled'
        if not permission_service.can(op.permission_action):
            return f'inventory_permission_{op.permission_action}_missing'
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
                'INVENTORY_OPERATION',
                None,
                new_values={'operation': operation_key, 'allowed': allowed, 'reason': reason, 'context': context, 'payload': payload or {}},
                details=f"inventory_operation:{operation_key}:{'allowed' if allowed else 'denied'}",
            )
        except Exception:
            pass


inventory_operation_policy = InventoryOperationPolicy()
