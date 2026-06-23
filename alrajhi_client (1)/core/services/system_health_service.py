# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any

from gateways.system_gateway import create_system_gateway, SystemGateway


class SystemHealthService:
    """Enterprise System Health Center.

    Database access is intentionally delegated to SystemGateway so core
    services remain outside direct SQLite/DatabaseConnection boundaries.
    """

    def __init__(self, gateway: SystemGateway | None = None):
        self.gateway = gateway or create_system_gateway()

    def ensure_schema(self, conn=None):
        # Compatibility no-op. Schema creation is owned by SystemGateway.
        return None

    def run_checks(self) -> Dict[str, Any]:
        return self.gateway.run_health_checks()


system_health_service = SystemHealthService()
