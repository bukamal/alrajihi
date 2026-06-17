from __future__ import annotations

import datetime
import os
from typing import Any

from alrajhi_server.database.connection import DB_PATH, get_db


class DebugRepository:
    """Read-only operational diagnostics for server API endpoints."""

    DEBUG_TABLES = [
        'users', 'items', 'categories', 'customers', 'suppliers', 'invoices',
        'invoice_lines', 'cashboxes', 'bank_accounts', 'vouchers', 'audit_log',
        'sales_returns', 'purchase_returns', 'bom', 'production_orders'
    ]
    HEALTH_TABLES = [
        'items', 'customers', 'suppliers', 'invoices', 'invoice_lines',
        'inventory_movements', 'warehouse_movements', 'inventory_ledger',
        'sales_returns', 'purchase_returns', 'production_orders', 'audit_log',
    ]

    @staticmethod
    def _count(db: Any, table: str) -> int | dict[str, str]:
        try:
            return int(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        except Exception as exc:
            return {'error': str(exc)}

    def status(self, user_id: Any) -> dict[str, Any]:
        db = get_db()
        user = None
        try:
            row = db.execute('SELECT id, username, full_name, role FROM users WHERE id=?', (user_id,)).fetchone()
            user = dict(row) if row else None
        except Exception:
            user = None
        return {
            'api_version': 2,
            'mode': 'server_api',
            'db_path': DB_PATH,
            'db_exists': os.path.exists(DB_PATH),
            'current_user_id': user_id,
            'current_user': user,
            'counts': {table: self._count(db, table) for table in self.DEBUG_TABLES},
        }

    def health(self, tolerance: str = '0') -> dict[str, Any]:
        db = get_db()
        counts = {table: self._count(db, table) for table in self.HEALTH_TABLES}
        try:
            ledger_entries = counts.get('inventory_ledger') if isinstance(counts.get('inventory_ledger'), int) else 0
            item_count = counts.get('items') if isinstance(counts.get('items'), int) else 0
            ledger = {
                'status': 'ok' if ledger_entries >= 0 else 'unknown',
                'ok': True,
                'entries': ledger_entries,
                'items': item_count,
                'tolerance': tolerance,
                'source': 'server_monitoring_endpoint',
            }
        except Exception as exc:
            ledger = {'status': 'unknown', 'ok': False, 'error': str(exc)[:300], 'source': 'server_monitoring_endpoint'}
        return {
            'status': 'ok',
            'mode': 'server_api',
            'db_path': DB_PATH,
            'db_exists': os.path.exists(DB_PATH),
            'counts': counts,
            'ledger': ledger,
            'checked_at': datetime.datetime.now().isoformat(timespec='seconds'),
        }
