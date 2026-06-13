# -*- coding: utf-8 -*-
"""Read-only production monitoring service.

Phase 35: a single application-level API for UI/diagnostics to check API,
Offline Queue, Ledger, and request health without touching DB/DAO directly.
"""
from __future__ import annotations

from typing import Dict, List

from gateways.monitoring_gateway import create_monitoring_gateway


class MonitoringService:
    def __init__(self):
        self._gateway = None

    def _get_gateway(self):
        if self._gateway is None:
            self._gateway = create_monitoring_gateway()
        return self._gateway

    def overview(self, tolerance: str = '0') -> Dict:
        return self._get_gateway().overview(tolerance=tolerance)

    def queue_health(self, limit: int = 20) -> Dict:
        return self._get_gateway().queue_health(limit=limit)

    def api_health(self) -> Dict:
        return self._get_gateway().api_health()

    def ledger_health(self, tolerance: str = '0') -> Dict:
        return self._get_gateway().ledger_health(tolerance=tolerance)

    def request_log(self, limit: int = 30) -> List[Dict]:
        return self._get_gateway().request_log(limit=limit)


monitoring_service = MonitoringService()
