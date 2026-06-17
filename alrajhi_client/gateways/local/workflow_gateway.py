# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from auth.session import UserSession
from database.connection import DatabaseConnection
from gateways.workflow_gateway import WorkflowGateway


class LocalWorkflowGateway(WorkflowGateway):
    DRAFT = 'DRAFT'
    SUBMITTED = 'SUBMITTED'
    APPROVED = 'APPROVED'
    POSTED = 'POSTED'
    CANCELLED = 'CANCELLED'
    VALID_STATUSES = {DRAFT, SUBMITTED, APPROVED, POSTED, CANCELLED}

    def _db(self) -> DatabaseConnection:
        return DatabaseConnection()

    def _normalize_status(self, status: Any) -> str:
        value = str(status or self.DRAFT).strip().upper()
        return value if value in self.VALID_STATUSES else self.DRAFT

    def _ensure_schema(self, conn) -> None:
        def cols(table):
            return {r[1] for r in conn.execute(f'PRAGMA table_info({table})').fetchall()}

        existing_tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if 'invoices' not in existing_tables:
            return
        invoice_cols = cols('invoices')
        additions = {
            'workflow_status': "TEXT DEFAULT 'DRAFT'",
            'submitted_at': 'TEXT',
            'submitted_by': 'TEXT',
            'approved_at': 'TEXT',
            'approved_by': 'TEXT',
            'posted_at': 'TEXT',
            'posted_by': 'TEXT',
            'cancelled_at': 'TEXT',
            'cancelled_by': 'TEXT',
            'deleted_by': 'TEXT',
        }
        for name, ddl in additions.items():
            if name not in invoice_cols:
                conn.execute(f'ALTER TABLE invoices ADD COLUMN {name} {ddl}')
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workflow_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                old_status TEXT,
                new_status TEXT NOT NULL,
                action TEXT NOT NULL,
                username TEXT,
                user_id TEXT,
                notes TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute('CREATE INDEX IF NOT EXISTS idx_workflow_events_entity ON workflow_events(entity_type, entity_id, created_at)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_invoices_workflow_status ON invoices(workflow_status)')

    def ensure_schema(self) -> None:
        db = self._db()
        if db.is_remote():
            return
        conn = db.get_connection()
        self._ensure_schema(conn)
        conn.commit()

    def transition_invoice(self, invoice_id: int, new_status: str, action: str, notes: str = '') -> str:
        db = self._db()
        new_status = self._normalize_status(new_status)
        if db.is_remote():
            result = db.get_rest_client().transition_invoice_workflow(invoice_id, new_status, action, notes)
            if isinstance(result, dict):
                return self._normalize_status(result.get('workflow_status') or new_status)
            return new_status

        conn = db.get_connection()
        self._ensure_schema(conn)
        row = conn.execute('SELECT * FROM invoices WHERE id=? AND deleted_at IS NULL', (invoice_id,)).fetchone()
        if not row:
            raise ValueError('الفاتورة غير موجودة')
        old_status = self._normalize_status(row['workflow_status'] if 'workflow_status' in row.keys() else row['status'])
        now = datetime.now().isoformat(timespec='seconds')
        user_id = UserSession.get_current_user_id()
        username = UserSession.get_current_username() or ''
        cols = {'workflow_status': new_status}
        if new_status == self.SUBMITTED:
            cols.update({'submitted_at': now, 'submitted_by': username})
        elif new_status == self.APPROVED:
            cols.update({'approved_at': now, 'approved_by': username})
        elif new_status == self.POSTED:
            cols.update({'posted_at': now, 'posted_by': username})
        elif new_status == self.CANCELLED:
            cols.update({'cancelled_at': now, 'cancelled_by': username})
        set_sql = ', '.join([f'{k}=?' for k in cols])
        conn.execute(f'UPDATE invoices SET {set_sql} WHERE id=?', list(cols.values()) + [invoice_id])
        conn.execute('''
            INSERT INTO workflow_events(entity_type, entity_id, old_status, new_status, action, username, user_id, notes, created_at)
            VALUES (?,?,?,?,?,?,?,?,?)
        ''', ('INVOICE', invoice_id, old_status, new_status, action, username, user_id, notes, now))
        conn.commit()
        return new_status

    def diagnostics(self) -> Dict[str, Any]:
        db = self._db()
        if db.is_remote():
            return {'mode': 'remote', 'checks': []}
        conn = db.get_connection()
        self._ensure_schema(conn)

        def count(status):
            return int(conn.execute('SELECT COUNT(*) FROM invoices WHERE deleted_at IS NULL AND COALESCE(workflow_status, ?) = ?', (self.DRAFT, status)).fetchone()[0])

        return {
            'mode': 'local',
            'draft': count(self.DRAFT),
            'submitted': count(self.SUBMITTED),
            'approved': count(self.APPROVED),
            'posted': count(self.POSTED),
            'cancelled': count(self.CANCELLED),
            'deleted': int(conn.execute('SELECT COUNT(*) FROM invoices WHERE deleted_at IS NOT NULL').fetchone()[0]),
        }
