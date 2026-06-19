# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from database.connection import DatabaseConnection
from gateways.approval_gateway import ApprovalGateway


class LocalApprovalGateway(ApprovalGateway):
    def is_remote(self) -> bool:
        return False

    def _db(self):
        return DatabaseConnection()

    def ensure_schema(self, conn=None) -> None:
        owns = conn is None
        if owns:
            db = self._db()
            if db.is_remote():
                return
            conn = db.get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS approval_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                amount TEXT DEFAULT '0',
                threshold_amount TEXT DEFAULT '0',
                status TEXT NOT NULL DEFAULT 'PENDING',
                requested_by TEXT,
                requested_at TEXT,
                decided_by TEXT,
                decided_at TEXT,
                decision_notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                UNIQUE(entity_type, entity_id)
            )
        """)
        conn.execute('CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests(status, entity_type)')
        if owns:
            conn.commit()

    def ensure_invoice_request(self, invoice: Dict[str, Any], threshold_amount: Any, requested_by: str, notes: str = '') -> Optional[int]:
        db = self._db()
        if db.is_remote() or not invoice or not invoice.get('id'):
            return None
        conn = db.get_connection()
        self.ensure_schema(conn)
        now = datetime.now().isoformat(timespec='seconds')
        row = conn.execute("SELECT id FROM approval_requests WHERE entity_type='INVOICE' AND entity_id=?", (invoice['id'],)).fetchone()
        if row:
            return int(row['id'])
        cur = conn.execute("""
            INSERT INTO approval_requests(entity_type, entity_id, amount, threshold_amount, status, requested_by, requested_at, created_at, updated_at, decision_notes)
            VALUES ('INVOICE', ?, ?, ?, 'PENDING', ?, ?, ?, ?, ?)
        """, (invoice['id'], str(invoice.get('total', 0)), str(threshold_amount), requested_by, now, now, now, notes or ''))
        conn.commit()
        return int(cur.lastrowid)

    def set_invoice_request_status(self, invoice_id: int, status: str, decided_by: str, notes: str = '') -> None:
        db = self._db()
        if db.is_remote():
            return
        conn = db.get_connection()
        self.ensure_schema(conn)
        now = datetime.now().isoformat(timespec='seconds')
        default_note = 'تم اعتماد الفاتورة' if status == 'APPROVED' else 'رفض الفاتورة'
        conn.execute("""
            UPDATE approval_requests SET status=?, decided_by=?, decided_at=?, decision_notes=?, updated_at=?
            WHERE entity_type='INVOICE' AND entity_id=?
        """, (status, decided_by, now, notes or default_note, now, invoice_id))
        conn.commit()

    def pending(self, limit: int = 200) -> List[Dict[str, Any]]:
        db = self._db()
        if db.is_remote():
            return []
        conn = db.get_connection()
        self.ensure_schema(conn)
        return [dict(r) for r in conn.execute("SELECT * FROM approval_requests WHERE status='PENDING' ORDER BY id DESC LIMIT ?", (int(limit or 200),)).fetchall()]
    def ensure_advanced_schema(self, conn=None) -> None:
        owns = conn is None
        if owns:
            db = self._db()
            if db.is_remote():
                return
            conn = db.get_connection()
        cur = conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS approval_matrix (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_type TEXT NOT NULL DEFAULT 'INVOICE',
                invoice_type TEXT,
                min_amount TEXT DEFAULT '0',
                max_amount TEXT,
                required_role TEXT NOT NULL,
                required_permission TEXT DEFAULT 'approval.approve',
                approval_order INTEGER NOT NULL DEFAULT 1,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS approval_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                approval_request_id INTEGER NOT NULL,
                step_order INTEGER NOT NULL,
                required_role TEXT NOT NULL,
                required_permission TEXT DEFAULT 'approval.approve',
                status TEXT DEFAULT 'PENDING',
                decided_by TEXT,
                decided_at TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(approval_request_id, step_order),
                FOREIGN KEY(approval_request_id) REFERENCES approval_requests(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_approval_steps_request
                ON approval_steps(approval_request_id, status, step_order);
        """)
        def _cols(table):
            try:
                return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
            except Exception:
                return set()
        for col, ddl in [
            ('invoice_type','TEXT'), ('min_amount',"TEXT DEFAULT '0'"), ('max_amount','TEXT'),
            ('required_permission',"TEXT DEFAULT 'approval.approve'"), ('approval_order','INTEGER DEFAULT 1'), ('is_active','INTEGER DEFAULT 1')
        ]:
            if col not in _cols('approval_matrix'):
                conn.execute(f"ALTER TABLE approval_matrix ADD COLUMN {col} {ddl}")
        conn.execute('CREATE INDEX IF NOT EXISTS idx_approval_matrix_scope ON approval_matrix(document_type, invoice_type, is_active, approval_order)')
        if owns:
            conn.commit()

    def matrix_for(self, document_type: str, invoice_type: str | None, amount: Any) -> List[Dict[str, Any]]:
        from decimal import Decimal, InvalidOperation
        def _decimal(value: Any) -> Decimal:
            try:
                return Decimal(str(value or '0'))
            except (InvalidOperation, ValueError):
                return Decimal('0')
        db = self._db()
        if db.is_remote():
            return []
        conn = db.get_connection()
        self.ensure_advanced_schema(conn)
        amt = _decimal(amount)
        rows = conn.execute("""
            SELECT * FROM approval_matrix
            WHERE document_type=? AND is_active=1
              AND (invoice_type IS NULL OR invoice_type=?)
            ORDER BY approval_order, id
        """, (document_type, invoice_type)).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            mn = _decimal(d.get('min_amount'))
            mx = d.get('max_amount')
            if amt >= mn and (mx is None or str(mx) == '' or amt < _decimal(mx)):
                result.append(d)
        seen = set(); out = []
        for d in result:
            key = int(d.get('approval_order') or 1)
            if key in seen:
                continue
            seen.add(key); out.append(d)
        return out

    def ensure_steps_for_request(self, approval_request_id: int, document_type: str = 'INVOICE', invoice_type: str | None = None, amount: Any = 0) -> int:
        db = self._db()
        if db.is_remote():
            return 0
        conn = db.get_connection()
        self.ensure_advanced_schema(conn)
        steps = self.matrix_for(document_type, invoice_type, amount)
        if not steps:
            steps = [{'approval_order': 1, 'required_role': 'manager', 'required_permission': 'approval.approve'}]
        for s in steps:
            conn.execute("""
                INSERT OR IGNORE INTO approval_steps(approval_request_id, step_order, required_role, required_permission, status)
                VALUES (?,?,?,?, 'PENDING')
            """, (approval_request_id, int(s.get('approval_order') or 1), str(s.get('required_role') or 'manager'), str(s.get('required_permission') or 'approval.approve')))
        conn.commit()
        return len(steps)

    def pending_step(self, approval_request_id: int) -> Optional[Dict[str, Any]]:
        db = self._db()
        if db.is_remote():
            return None
        conn = db.get_connection()
        self.ensure_advanced_schema(conn)
        row = conn.execute("""
            SELECT * FROM approval_steps
            WHERE approval_request_id=? AND status='PENDING'
            ORDER BY step_order LIMIT 1
        """, (int(approval_request_id),)).fetchone()
        return dict(row) if row else None

    def approve_current_step(self, approval_request_id: int, username: str, notes: str = '') -> Dict[str, Any]:
        db = self._db()
        if db.is_remote():
            return {'status': 'remote_unsupported'}
        conn = db.get_connection()
        self.ensure_advanced_schema(conn)
        step = self.pending_step(approval_request_id)
        if not step:
            return {'status': 'already_complete'}
        now = datetime.now().isoformat(timespec='seconds')
        conn.execute("""
            UPDATE approval_steps SET status='APPROVED', decided_by=?, decided_at=?, notes=?
            WHERE id=?
        """, (username, now, notes or 'approved', step['id']))
        remaining = conn.execute("""
            SELECT COUNT(*) FROM approval_steps WHERE approval_request_id=? AND status='PENDING'
        """, (approval_request_id,)).fetchone()[0]
        if int(remaining) == 0:
            conn.execute("""
                UPDATE approval_requests SET status='APPROVED', decided_by=?, decided_at=?, decision_notes=?, updated_at=?
                WHERE id=?
            """, (username, now, notes or 'multi-level approved', now, approval_request_id))
            req = conn.execute("SELECT entity_type, entity_id FROM approval_requests WHERE id=?", (approval_request_id,)).fetchone()
            if req and req['entity_type'] == 'INVOICE':
                conn.execute("UPDATE invoices SET workflow_status='APPROVED', approved_by=?, approved_at=? WHERE id=?", (username, now, req['entity_id']))
        conn.commit()
        return {'status': 'approved', 'remaining_steps': int(remaining), 'step_order': step.get('step_order')}

    def request_status(self, approval_request_id: int) -> Dict[str, Any]:
        db = self._db()
        if db.is_remote():
            return {}
        conn = db.get_connection()
        self.ensure_advanced_schema(conn)
        req = conn.execute('SELECT * FROM approval_requests WHERE id=?', (int(approval_request_id),)).fetchone()
        steps = [dict(r) for r in conn.execute('SELECT * FROM approval_steps WHERE approval_request_id=? ORDER BY step_order', (int(approval_request_id),)).fetchall()]
        return {'request': dict(req) if req else None, 'steps': steps}

