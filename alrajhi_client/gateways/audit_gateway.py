# -*- coding: utf-8 -*-
"""Audit gateway contract and factory.

Phase 13 moves direct audit_log database writes out of core/services and behind
an infrastructure gateway.  The server remains authoritative in remote mode.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, Tuple


class AuditGateway(ABC):
    @abstractmethod
    def log(self, action: str, entity_type: str, entity_id: Optional[int] = None,
            old_values: Any = None, new_values: Any = None, details: str = '',
            source: str = 'USER', ip_address: str = '127.0.0.1') -> None:
        raise NotImplementedError

    @abstractmethod
    def list_logs(self, limit: int = 1000, offset: int = 0, user_id: int | None = None,
                  action: str | None = None, table_name: str | None = None,
                  start_date: str | None = None, end_date: str | None = None) -> Tuple[List[Dict], int]:
        raise NotImplementedError

    @abstractmethod
    def delete_old_logs(self, days: int = 90) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_remote(self) -> bool:
        raise NotImplementedError


def create_audit_gateway() -> AuditGateway:
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.audit_gateway import RemoteAuditGateway
        return RemoteAuditGateway()

    from gateways.local.audit_gateway import LocalAuditGateway
    return LocalAuditGateway(db)
