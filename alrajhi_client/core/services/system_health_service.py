# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, List
import json, os, sqlite3, tempfile, shutil


class SystemHealthService:
    """Enterprise System Health Center."""

    def _db(self):
        from database.connection import DatabaseConnection
        return DatabaseConnection()

    def ensure_schema(self, conn=None):
        owns = conn is None
        if owns:
            db = self._db()
            if db.is_remote():
                return
            conn = db.get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS system_health_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_key TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                details TEXT,
                checked_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        if owns:
            conn.commit()

    def _count(self, conn, sql, params=()):
        try:
            return int(conn.execute(sql, params).fetchone()[0] or 0)
        except Exception:
            return -1

    def run_checks(self) -> Dict[str, Any]:
        db = self._db()
        if db.is_remote():
            return {'overall': 'UNKNOWN', 'checks': [{'key':'database','status':'UNKNOWN','message':'Remote mode'}]}
        conn = db.get_connection()
        self.ensure_schema(conn)
        checks: List[Dict[str, Any]] = []

        def add(key, status, message, details=None):
            checks.append({'key': key, 'status': status, 'message': message, 'details': details or {}})
            try:
                conn.execute(
                    'INSERT INTO system_health_checks(check_key,status,message,details,checked_at) VALUES (?,?,?,?,?)',
                    (key, status, message, json.dumps(details or {}, ensure_ascii=False), datetime.now().isoformat(timespec='seconds'))
                )
            except Exception:
                pass

        required_tables = ['users','invoices','invoice_lines','approval_requests','approval_steps','accounts','journal_entries','journal_lines','roles','permissions']
        missing = []
        for table in required_tables:
            ok = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
            if not ok:
                missing.append(table)
        add('database_schema', 'GREEN' if not missing else 'RED', 'Schema OK' if not missing else 'Missing tables', {'missing': missing})

        pending = self._count(conn, "SELECT COUNT(*) FROM approval_requests WHERE status='PENDING'")
        add('pending_approvals', 'GREEN' if pending == 0 else 'YELLOW', f'{pending} pending approval request(s)', {'count': pending})

        unposted = self._count(conn, "SELECT COUNT(*) FROM invoices WHERE COALESCE(workflow_status,'DRAFT')='APPROVED'")
        add('unposted_documents', 'GREEN' if unposted == 0 else 'YELLOW', f'{unposted} approved but unposted invoice(s)', {'count': unposted})

        sec = self._count(conn, "SELECT COUNT(*) FROM security_events WHERE created_at >= datetime('now','-7 days')") if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='security_events'").fetchone() else 0
        add('security_events_7d', 'GREEN' if sec == 0 else 'YELLOW', f'{sec} security event(s) in last 7 days', {'count': sec})

        imbalance = 0
        try:
            rows = conn.execute("""
                SELECT je.id, COALESCE(SUM(CAST(jl.debit AS REAL)),0) d, COALESCE(SUM(CAST(jl.credit AS REAL)),0) c
                FROM journal_entries je LEFT JOIN journal_lines jl ON jl.journal_entry_id=je.id
                GROUP BY je.id HAVING ABS(d-c) > 0.005
            """).fetchall()
            imbalance = len(rows)
        except Exception:
            imbalance = -1
        add('journal_balance', 'GREEN' if imbalance == 0 else 'RED', f'{imbalance} imbalanced journal(s)', {'count': imbalance})

        overall = 'GREEN'
        if any(c['status'] == 'RED' for c in checks):
            overall = 'RED'
        elif any(c['status'] == 'YELLOW' for c in checks):
            overall = 'YELLOW'
        try:
            conn.commit()
        except Exception:
            pass
        return {'overall': overall, 'checked_at': datetime.now().isoformat(timespec='seconds'), 'checks': checks}


system_health_service = SystemHealthService()
