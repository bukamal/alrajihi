# -*- coding: utf-8 -*-
from __future__ import annotations

from gateways.system_gateway import create_system_gateway


class ProductionValidationService:
    """Phase 159 recovery/stress validation helpers.

    Data-access work is intentionally delegated to SystemGateway so service
    code does not cross the UI/service -> database boundary.
    """

    def __init__(self, gateway=None):
        self.gateway = gateway or create_system_gateway()

    def ensure_schema(self, conn=None):
        # Backward-compatible no-op. Schema creation is handled inside the gateway.
        if conn is not None and hasattr(self.gateway, '_ensure_validation_runs_table'):
            self.gateway._ensure_validation_runs_table(conn)

    def _record(self, run_type, status, summary, details):
        self.gateway.record_validation_run(run_type, status, summary, details)

    def validate_backup_restore(self):
        return self.gateway.validate_backup_restore()

    def run_stress_smoke(self, invoice_count=200):
        return self.gateway.run_stress_smoke(int(invoice_count or 200))


production_validation_service = ProductionValidationService()
