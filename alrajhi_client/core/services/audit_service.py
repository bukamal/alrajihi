# -*- coding: utf-8 -*-
"""Audit log application service.

Calls are best-effort: audit failure must never break the business operation
that already succeeded.  Phase 13 routes persistence through AuditGateway so
core services do not access DatabaseConnection directly.
"""
from __future__ import annotations

from typing import Any, Optional, Dict, List, Tuple

from gateways.audit_gateway import create_audit_gateway


class AuditService:
    def __init__(self):
        self._gateway = None

    def _get_gateway(self):
        if self._gateway is None:
            self._gateway = create_audit_gateway()
        return self._gateway

    def log(self, action: str, entity_type: str, entity_id: Optional[int] = None,
            old_values: Any = None, new_values: Any = None, details: str = '',
            source: str = 'USER', ip_address: str = '127.0.0.1',
            audit_scope: str = '', permission_key: str = '', branch_id: Any = None,
            event_category: str = '') -> None:
        try:
            self._get_gateway().log(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_values=old_values,
                new_values=new_values,
                details=details,
                source=source,
                ip_address=ip_address,
                audit_scope=audit_scope,
                permission_key=permission_key,
                branch_id=branch_id,
                event_category=event_category,
            )
        except Exception:
            # Audit must not interrupt business workflows.
            pass

    def log_shell_event(self, event_key: str, *, entity_id=None, old_values=None, new_values=None, details: str = '', source: str = 'CONTRACT') -> None:
        try:
            from workspace.audit.audit_event_policy import log_contract_event
            log_contract_event(event_key, entity_id=entity_id, old_values=old_values, new_values=new_values, details=details, source=source)
        except Exception:
            pass


    def list_logs(self, limit: int = 1000, offset: int = 0, user_id: int | None = None,
                  action: str | None = None, table_name: str | None = None,
                  start_date: str | None = None, end_date: str | None = None) -> Tuple[List[Dict], int]:
        return self._get_gateway().list_logs(
            limit=limit, offset=offset, user_id=user_id, action=action,
            table_name=table_name, start_date=start_date, end_date=end_date,
        )

    def delete_old_logs(self, days: int = 90) -> None:
        self._get_gateway().delete_old_logs(days)


audit_service = AuditService()
