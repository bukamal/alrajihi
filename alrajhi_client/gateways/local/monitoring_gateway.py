# -*- coding: utf-8 -*-
"""Read-only runtime monitoring implementation.

This adapter deliberately keeps direct database/offline-queue access in the
local gateway layer.  It supports both local mode and client/remote mode:
- local mode: inspect local SQLite + local ledger DAO
- client mode: call remote monitoring endpoint where available, and always
  inspect the local offline queue because it lives on the client device.
"""
from __future__ import annotations

import datetime
from typing import Dict, List

from gateways.monitoring_gateway import MonitoringGateway


def _database_connection_cls():
    from database.connection import DatabaseConnection
    return DatabaseConnection


def _offline_queue():
    from database.connection import offline_queue
    return offline_queue


class LocalMonitoringGateway(MonitoringGateway):
    CRITICAL_QUEUE_STATUSES = {'failed'}

    def _db(self):
        return _database_connection_cls()()

    def is_remote(self) -> bool:
        return self._db().is_remote()

    def _safe_count(self, table: str) -> int | Dict:
        try:
            row = self._db().execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            return int(row[0] or 0)
        except Exception as exc:
            return {'error': str(exc)[:300]}

    def _local_counts(self) -> Dict:
        tables = [
            'items', 'customers', 'suppliers', 'invoices', 'invoice_lines',
            'inventory_movements', 'warehouse_movements', 'inventory_ledger',
            'sales_returns', 'purchase_returns', 'production_orders', 'audit_log',
        ]
        return {table: self._safe_count(table) for table in tables}

    def queue_health(self, limit: int = 20) -> Dict:
        queue = _offline_queue()
        rows = queue.get_recent_requests(max(int(limit or 20), 1))
        counts = {'pending': 0, 'sent': 0, 'failed': 0, 'other': 0}
        max_attempts = 0
        failed_rows = []
        pending_rows = []
        for row in rows:
            status = row.get('status') or 'pending'
            if status in counts:
                counts[status] += 1
            else:
                counts['other'] += 1
            attempts = int(row.get('attempts') or 0)
            max_attempts = max(max_attempts, attempts)
            if status == 'failed':
                failed_rows.append(row)
            elif status == 'pending':
                pending_rows.append(row)
        pending_total = queue.count_pending()
        status = 'ok'
        if failed_rows:
            status = 'critical'
        elif pending_total:
            status = 'warning'
        return {
            'status': status,
            'pending': pending_total,
            'recent_counts': counts,
            'max_attempts': max_attempts,
            'failed_recent': failed_rows[:10],
            'pending_recent': pending_rows[:10],
            'checked_at': datetime.datetime.now().isoformat(timespec='seconds'),
        }

    def api_health(self) -> Dict:
        db = self._db()
        info = {
            'mode': getattr(db, 'mode', 'local'),
            'server_url': getattr(db, 'server_url', ''),
            'status': 'local' if not db.is_remote() else 'unknown',
        }
        if not db.is_remote():
            return {**info, 'ok': True, 'message': 'Local SQLite mode'}
        try:
            # Prefer the existing server-control diagnostic because it validates
            # basic server reachability without requiring UI access.
            from core import server_control
            diag = server_control.server_diagnostics(db.server_url, timeout=3.0, require_routes=False)
            ok = bool(diag.get('ok')) if isinstance(diag, dict) else False
            return {**info, 'ok': ok, 'status': 'ok' if ok else 'down', 'diagnostics': diag}
        except Exception as exc:
            return {**info, 'ok': False, 'status': 'down', 'error': str(exc)[:500]}

    def ledger_health(self, tolerance: str = '0') -> Dict:
        db = self._db()
        if db.is_remote():
            rest = db.get_rest_client()
            if rest and hasattr(rest, 'get_monitoring_health'):
                try:
                    remote = rest.get_monitoring_health(tolerance=tolerance)
                    ledger = (remote or {}).get('ledger') or {}
                    ledger['source'] = 'remote_monitoring_endpoint'
                    return ledger
                except Exception as exc:
                    return {'status': 'unknown', 'ok': False, 'error': str(exc)[:500], 'source': 'remote_monitoring_endpoint'}
            return {'status': 'unknown', 'ok': False, 'error': 'No remote monitoring method available'}
        try:
            from database.dao.inventory_ledger_dao import InventoryLedgerDAO
            dao = InventoryLedgerDAO()
            health = dao.health_report(tolerance=tolerance)
            readiness = dao.readiness_gate(tolerance=tolerance)
            return {
                'status': 'ok' if readiness.get('safe_for_dual_read') else 'warning',
                'ok': bool(readiness.get('safe_for_dual_read')),
                'health': health,
                'readiness': readiness,
                'source': 'local_ledger_dao',
            }
        except Exception as exc:
            return {'status': 'unknown', 'ok': False, 'error': str(exc)[:500], 'source': 'local_ledger_dao'}

    def request_log(self, limit: int = 30) -> List[Dict]:
        try:
            from database.connection_rest import get_request_log
            rows = get_request_log()
            return list(rows)[-int(limit or 30):]
        except Exception:
            return []

    def overview(self, tolerance: str = '0') -> Dict:
        db = self._db()
        api = self.api_health()
        queue = self.queue_health(limit=30)
        ledger = self.ledger_health(tolerance=tolerance)
        request_log = self.request_log(limit=20)
        critical = []
        warnings = []
        if api.get('status') == 'down':
            critical.append('api_down')
        if queue.get('status') == 'critical':
            critical.append('offline_queue_failed_requests')
        elif queue.get('status') == 'warning':
            warnings.append('offline_queue_pending_requests')
        if ledger.get('status') not in {'ok', 'local'} and not ledger.get('ok'):
            warnings.append('ledger_not_ready')
        failed_http = [r for r in request_log if not r.get('ok')]
        if failed_http:
            warnings.append('recent_api_errors')
        status = 'critical' if critical else ('warning' if warnings else 'ok')
        return {
            'status': status,
            'critical': critical,
            'warnings': warnings,
            'mode': getattr(db, 'mode', 'local'),
            'data_source': db.data_source_label() if hasattr(db, 'data_source_label') else '',
            'api': api,
            'queue': queue,
            'ledger': ledger,
            'request_log': request_log,
            'counts': {} if db.is_remote() else self._local_counts(),
            'checked_at': datetime.datetime.now().isoformat(timespec='seconds'),
        }
