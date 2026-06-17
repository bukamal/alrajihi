from __future__ import annotations

import datetime
import os
import shutil
import sqlite3
import tempfile
from typing import Any

from alrajhi_server.database.connection import get_db


class GovernanceRepository:
    """Persistence and diagnostics boundary for enterprise governance routes."""

    def __init__(self) -> None:
        self._db = get_db()

    def is_admin(self, user_id: str) -> bool:
        row = self._db.execute('SELECT role FROM users WHERE id=?', (str(user_id),)).fetchone()
        return bool(row and row['role'] == 'admin')

    def list_active_approval_matrix(self) -> list[dict]:
        rows = self._db.execute(
            'SELECT * FROM approval_matrix WHERE is_active=1 ORDER BY document_type, invoice_type, approval_order, id'
        ).fetchall()
        return [dict(r) for r in rows]

    def add_approval_matrix(self, data: dict[str, Any]) -> int:
        cur = self._db.execute("""
            INSERT INTO approval_matrix(document_type, invoice_type, min_amount, max_amount, required_role, required_permission, approval_order, is_active)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            data.get('document_type','INVOICE'), data.get('invoice_type'), str(data.get('min_amount','0')),
            None if data.get('max_amount') in (None, '') else str(data.get('max_amount')),
            data.get('required_role','manager'), data.get('required_permission','approval.approve'),
            int(data.get('approval_order',1)), int(data.get('is_active',1))
        ))
        self._db.commit()
        return int(cur.lastrowid)

    def table_exists(self, table_name: str) -> bool:
        row = self._db.execute('SELECT 1 FROM sqlite_master WHERE type="table" AND name=?', (table_name,)).fetchone()
        return bool(row)

    def count_pending_approvals(self) -> int:
        try:
            return int(self._db.execute("SELECT COUNT(*) FROM approval_requests WHERE status='PENDING'").fetchone()[0] or 0)
        except Exception:
            return -1

    def count_approved_unposted_invoices(self) -> int:
        try:
            return int(self._db.execute("SELECT COUNT(*) FROM invoices WHERE COALESCE(workflow_status,'DRAFT')='APPROVED'").fetchone()[0] or 0)
        except Exception:
            return -1

    def validate_backup_restore(self, db_path: str) -> dict[str, Any]:
        tmp = tempfile.mkdtemp(prefix='alrajhi_srv_restore_')
        try:
            backup = os.path.join(tmp, 'backup.sqlite')
            shutil.copy2(db_path, backup)
            test = sqlite3.connect(backup)
            try:
                integrity = test.execute('PRAGMA integrity_check').fetchone()[0]
                tables = test.execute('SELECT COUNT(*) FROM sqlite_master WHERE type="table"').fetchone()[0]
            finally:
                test.close()
            return {'status': 'PASSED' if integrity == 'ok' else 'FAILED', 'integrity_check': integrity, 'tables': tables}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def run_stress_smoke(self, count: int) -> dict[str, Any]:
        self._db.execute('CREATE TABLE IF NOT EXISTS stress_probe(id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, amount TEXT, created_at TEXT)')
        for i in range(count):
            self._db.execute(
                'INSERT INTO stress_probe(ref, amount, created_at) VALUES (?,?,?)',
                (f'STRESS-{i}', str(i), datetime.datetime.now().isoformat(timespec='seconds'))
            )
        total = self._db.execute('SELECT COUNT(*) FROM stress_probe').fetchone()[0]
        self._db.commit()
        return {'status': 'PASSED', 'inserted': count, 'total_probe_rows': total}


def get_governance_repository() -> GovernanceRepository:
    return GovernanceRepository()
