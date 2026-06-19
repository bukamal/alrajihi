# -*- coding: utf-8 -*-
"""Report operation governance (Phase 214).

Reports are read-only, but they can expose sensitive profit, cost, cash, bank,
inventory and ledger data.  This policy centralizes report view/export checks so
widgets, mixins and future services do not duplicate permission/settings logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from core.services.audit_service import audit_service


@dataclass(frozen=True)
class ReportOperation:
    key: str
    setting_key: str
    permission_action: str
    label_key: str


class ReportOperationPolicy:
    OP_VIEW = 'view'
    OP_EXPORT = 'export'

    def _permission_service(self):
        from core.services.permission_service import permission_service
        return permission_service

    def _settings_service(self):
        from core.services.settings_service import settings_service
        return settings_service

    def _operations(self) -> Dict[str, ReportOperation]:
        ps = self._permission_service()
        return {
            self.OP_VIEW: ReportOperation(self.OP_VIEW, 'allow_view', ps.ACTION_VIEW_REPORTS, 'reports.operation.view'),
            self.OP_EXPORT: ReportOperation(self.OP_EXPORT, 'allow_export', ps.ACTION_EXPORT_REPORTS, 'reports.operation.export'),
        }

    def settings(self) -> Dict[str, Any]:
        try:
            return self._settings_service().get_report_settings()
        except Exception:
            return {'enabled': True, 'operations': {}}

    def is_enabled(self) -> bool:
        return bool(self.settings().get('enabled', True))

    def operation_allowed_by_settings(self, operation_key: str) -> bool:
        if not self.is_enabled() and operation_key != self.OP_VIEW:
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
            return 'unknown_report_operation'
        if not self.is_enabled() and operation_key != self.OP_VIEW:
            return 'reports_disabled'
        if not self.operation_allowed_by_settings(operation_key):
            return f'reports_setting_{op.setting_key}_disabled'
        if not self._permission_service().can(op.permission_action):
            return f'reports_permission_{op.permission_action}_missing'
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
                'REPORT_OPERATION',
                None,
                new_values={
                    'operation': operation_key,
                    'allowed': bool(allowed),
                    'reason': reason,
                    'context': context,
                    'payload': payload or {},
                },
                details=f"report operation {operation_key}: {'allowed' if allowed else reason}",
            )
        except Exception:
            pass


report_operation_policy = ReportOperationPolicy()
