# -*- coding: utf-8 -*-
"""Finance/cash-bank operation governance (Phase 203)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from core.services.audit_service import audit_service


@dataclass(frozen=True)
class FinanceOperation:
    key: str
    setting_key: str
    permission_action: str
    label_key: str


class FinanceOperationPolicy:
    OP_USE = 'use'
    OP_CASHBOX_CREATE = 'cashbox_create'
    OP_CASHBOX_EDIT = 'cashbox_edit'
    OP_CASHBOX_ARCHIVE = 'cashbox_archive'
    OP_BANK_CREATE = 'bank_create'
    OP_BANK_EDIT = 'bank_edit'
    OP_BANK_ARCHIVE = 'bank_archive'
    OP_MOVEMENTS_VIEW = 'movements_view'
    OP_SHIFTS_VIEW = 'shifts_view'
    OP_VOUCHER_CREATE = 'voucher_create'
    OP_VOUCHER_EDIT = 'voucher_edit'
    OP_VOUCHER_DELETE = 'voucher_delete'
    OP_VOUCHER_PRINT = 'voucher_print'
    OP_VOUCHER_VIEW = 'voucher_view'

    def _permission_service(self):
        from core.services.permission_service import permission_service
        return permission_service

    def _settings_service(self):
        from core.services.settings_service import settings_service
        return settings_service

    def _operations(self) -> Dict[str, FinanceOperation]:
        ps = self._permission_service()
        return {
            self.OP_USE: FinanceOperation(self.OP_USE, 'allow_use', ps.ACTION_USE_FINANCE, 'finance.operation.use'),
            self.OP_CASHBOX_CREATE: FinanceOperation(self.OP_CASHBOX_CREATE, 'allow_cashbox_create', ps.ACTION_CASHBOX_CREATE, 'finance.operation.cashbox_create'),
            self.OP_CASHBOX_EDIT: FinanceOperation(self.OP_CASHBOX_EDIT, 'allow_cashbox_edit', ps.ACTION_CASHBOX_EDIT, 'finance.operation.cashbox_edit'),
            self.OP_CASHBOX_ARCHIVE: FinanceOperation(self.OP_CASHBOX_ARCHIVE, 'allow_cashbox_archive', ps.ACTION_CASHBOX_ARCHIVE, 'finance.operation.cashbox_archive'),
            self.OP_BANK_CREATE: FinanceOperation(self.OP_BANK_CREATE, 'allow_bank_create', ps.ACTION_BANK_CREATE, 'finance.operation.bank_create'),
            self.OP_BANK_EDIT: FinanceOperation(self.OP_BANK_EDIT, 'allow_bank_edit', ps.ACTION_BANK_EDIT, 'finance.operation.bank_edit'),
            self.OP_BANK_ARCHIVE: FinanceOperation(self.OP_BANK_ARCHIVE, 'allow_bank_archive', ps.ACTION_BANK_ARCHIVE, 'finance.operation.bank_archive'),
            self.OP_MOVEMENTS_VIEW: FinanceOperation(self.OP_MOVEMENTS_VIEW, 'allow_movements_view', ps.ACTION_FINANCE_MOVEMENTS_VIEW, 'finance.operation.movements_view'),
            self.OP_SHIFTS_VIEW: FinanceOperation(self.OP_SHIFTS_VIEW, 'allow_shifts_view', ps.ACTION_FINANCE_SHIFTS_VIEW, 'finance.operation.shifts_view'),
            self.OP_VOUCHER_CREATE: FinanceOperation(self.OP_VOUCHER_CREATE, 'allow_voucher_create', ps.ACTION_VOUCHER_CREATE, 'finance.operation.voucher_create'),
            self.OP_VOUCHER_EDIT: FinanceOperation(self.OP_VOUCHER_EDIT, 'allow_voucher_edit', ps.ACTION_VOUCHER_EDIT, 'finance.operation.voucher_edit'),
            self.OP_VOUCHER_DELETE: FinanceOperation(self.OP_VOUCHER_DELETE, 'allow_voucher_delete', ps.ACTION_VOUCHER_DELETE, 'finance.operation.voucher_delete'),
            self.OP_VOUCHER_PRINT: FinanceOperation(self.OP_VOUCHER_PRINT, 'allow_voucher_print', ps.ACTION_VOUCHER_PRINT, 'finance.operation.voucher_print'),
            self.OP_VOUCHER_VIEW: FinanceOperation(self.OP_VOUCHER_VIEW, 'allow_voucher_view', ps.ACTION_VOUCHER_VIEW, 'finance.operation.voucher_view'),
        }

    def settings(self) -> Dict[str, Any]:
        try:
            return self._settings_service().get_finance_settings()
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
            return 'unknown_finance_operation'
        if not self.is_enabled() and operation_key != self.OP_USE:
            return 'finance_disabled'
        if not self.operation_allowed_by_settings(operation_key):
            return f'finance_setting_{op.setting_key}_disabled'
        if not self._permission_service().can(op.permission_action):
            return f'finance_permission_{op.permission_action}_missing'
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
                'FINANCE_OPERATION',
                None,
                new_values={'operation': operation_key, 'allowed': allowed, 'reason': reason, 'context': context, 'payload': payload or {}},
                details=f"finance_operation:{operation_key}:{'allowed' if allowed else 'denied'}",
            )
        except Exception:
            pass


finance_operation_policy = FinanceOperationPolicy()
