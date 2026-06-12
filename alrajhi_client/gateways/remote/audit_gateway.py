# -*- coding: utf-8 -*-
"""Remote audit gateway adapter.

In client/server mode, audit entries should be emitted by the authoritative
server API.  Desktop-side audit writes are therefore intentionally ignored.
"""
from __future__ import annotations

from typing import Any, Optional, Dict, List, Tuple

from database.connection import DatabaseConnection
from gateways.audit_gateway import AuditGateway


class RemoteAuditGateway(AuditGateway):
    def is_remote(self) -> bool:
        return True

    def log(self, action: str, entity_type: str, entity_id: Optional[int] = None,
            old_values: Any = None, new_values: Any = None, details: str = '',
            source: str = 'USER', ip_address: str = '127.0.0.1') -> None:
        return None


    def list_logs(self, limit: int = 1000, offset: int = 0, user_id: int | None = None,
                  action: str | None = None, table_name: str | None = None,
                  start_date: str | None = None, end_date: str | None = None) -> Tuple[List[Dict], int]:
        client = DatabaseConnection().get_rest_client()
        logs = client.get_audit_log(limit=max(limit + offset, 2000), offset=0)
        filtered = logs
        if user_id:
            filtered = [l for l in filtered if l.get('user_id') == user_id]
        if action and action != "الكل":
            filtered = [l for l in filtered if l.get('action') == action]
        if table_name and table_name != "الكل":
            filtered = [l for l in filtered if l.get('table_name') == table_name or l.get('entity_type') == table_name]
        if start_date:
            filtered = [l for l in filtered if (l.get('timestamp') or l.get('event_time') or '')[:10] >= start_date]
        if end_date:
            filtered = [l for l in filtered if (l.get('timestamp') or l.get('event_time') or '')[:10] <= end_date]
        total = len(filtered)
        return filtered[offset:offset + limit], total

    def delete_old_logs(self, days: int = 90) -> None:
        DatabaseConnection().get_rest_client().delete_old_audit_logs(days)
