# -*- coding: utf-8 -*-
"""Production monitoring gateway contract.

Phase 35 adds read-only operational diagnostics for Sync/API/Ledger health.
The UI and services must not inspect DatabaseConnection, offline_queue, or SQL
objects directly; all runtime checks stay behind this gateway.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class MonitoringGateway(ABC):
    @abstractmethod
    def is_remote(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def overview(self, tolerance: str = '0') -> Dict:
        raise NotImplementedError

    @abstractmethod
    def queue_health(self, limit: int = 20) -> Dict:
        raise NotImplementedError

    @abstractmethod
    def api_health(self) -> Dict:
        raise NotImplementedError

    @abstractmethod
    def ledger_health(self, tolerance: str = '0') -> Dict:
        raise NotImplementedError

    @abstractmethod
    def request_log(self, limit: int = 30) -> List[Dict]:
        raise NotImplementedError


def create_monitoring_gateway() -> MonitoringGateway:
    from gateways.local.monitoring_gateway import LocalMonitoringGateway
    return LocalMonitoringGateway()
