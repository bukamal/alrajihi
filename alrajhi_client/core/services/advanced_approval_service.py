# -*- coding: utf-8 -*-
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Any, Dict, List, Optional

from auth.session import UserSession
from core.services.rbac_service import rbac_service
from core.services.audit_service import audit_service
from core.services.permission_service import permission_service


class AdvancedApprovalService:
    """Multi-level approval engine.

    This service complements the older ApprovalService. It stores approval matrices
    and ordered approval steps per approval request. A request is APPROVED only when
    every required step is approved in order.
    """

    def _db(self):
        from database.connection import DatabaseConnection
        return DatabaseConnection()

    def _decimal(self, value: Any) -> Decimal:
        try:
            return Decimal(str(value or '0'))
        except (InvalidOperation, ValueError):
            return Decimal('0')

    def ensure_schema(self, conn=None) -> None:
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
        db = self._db()
        if db.is_remote():
            return []
        conn = db.get_connection()
        self.ensure_schema(conn)
        amt = self._decimal(amount)
        rows = conn.execute("""
            SELECT * FROM approval_matrix
            WHERE document_type=? AND is_active=1
              AND (invoice_type IS NULL OR invoice_type=?)
            ORDER BY approval_order, id
        """, (document_type, invoice_type)).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            mn = self._decimal(d.get('min_amount'))
            mx = d.get('max_amount')
            if amt >= mn and (mx is None or str(mx) == '' or amt < self._decimal(mx)):
                result.append(d)
        # deduplicate by approval_order, keep the first most specific row
        seen = set(); out = []
        for d in result:
            key = int(d.get('approval_order') or 1)
            if key in seen:
                continue
            seen.add(key); out.append(d)
        return out

    def ensure_steps_for_request(self, approval_request_id: int, document_type: str='INVOICE', invoice_type: str | None=None, amount: Any=0) -> int:
        db = self._db()
        if db.is_remote():
            return 0
        conn = db.get_connection()
        self.ensure_schema(conn)
        steps = self.matrix_for(document_type, invoice_type, amount)
        if not steps:
            # fallback single-step approval
            steps = [{'approval_order': 1, 'required_role': 'manager', 'required_permission': 'approval.approve'}]
        for s in steps:
            conn.execute("""
                INSERT OR IGNORE INTO approval_steps(approval_request_id, step_order, required_role, required_permission, status)
                VALUES (?,?,?,?, 'PENDING')
            """, (approval_request_id, int(s.get('approval_order') or 1), str(s.get('required_role') or 'manager'), str(s.get('required_permission') or 'approval.approve')))
        conn.commit()
        return len(steps)

    def ensure_invoice_steps(self, invoice: Dict[str, Any]) -> int:
        if not invoice or not invoice.get('id'):
            return 0
        from core.services.approval_service import approval_service
        request_id = approval_service.ensure_invoice_request(invoice, 'multi-level approval')
        if not request_id:
            return 0
        return self.ensure_steps_for_request(request_id, 'INVOICE', invoice.get('type'), invoice.get('total'))

    def pending_step(self, approval_request_id: int) -> Optional[Dict[str, Any]]:
        db = self._db()
        if db.is_remote():
            return None
        conn = db.get_connection()
        self.ensure_schema(conn)
        row = conn.execute("""
            SELECT * FROM approval_steps
            WHERE approval_request_id=? AND status='PENDING'
            ORDER BY step_order LIMIT 1
        """, (int(approval_request_id),)).fetchone()
        return dict(row) if row else None

    def approve_current_step(self, approval_request_id: int, notes: str='') -> Dict[str, Any]:
        db = self._db()
        if db.is_remote():
            return {'status': 'remote_unsupported'}
        conn = db.get_connection()
        self.ensure_schema(conn)
        step = self.pending_step(approval_request_id)
        if not step:
            return {'status': 'already_complete'}
        perm = step.get('required_permission') or 'approval.approve'
        role = (step.get('required_role') or '').lower()
        user_roles = [r.lower() for r in rbac_service.effective_user_roles()]
        if role and role not in user_roles and 'admin' not in user_roles:
            permission_service.log_event('APPROVAL_DENIED', action=perm, allowed=False, reason='required_role_missing', context=str(approval_request_id))
            raise PermissionError(f'تتطلب هذه الخطوة دور: {role}')
        if not rbac_service.has_permission(perm):
            permission_service.log_event('APPROVAL_DENIED', action=perm, allowed=False, reason='permission_missing', context=str(approval_request_id))
            raise PermissionError(f'تتطلب هذه الخطوة صلاحية: {perm}')
        now = datetime.now().isoformat(timespec='seconds')
        username = UserSession.get_current_username() or UserSession.get_current_user_id() or ''
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
        audit_service.log('APPROVE_STEP', 'APPROVAL_REQUEST', approval_request_id, new_values={'step': step.get('step_order'), 'remaining': int(remaining)}, details=notes)
        return {'status': 'approved', 'remaining_steps': int(remaining)}

    def request_status(self, approval_request_id: int) -> Dict[str, Any]:
        db = self._db()
        if db.is_remote():
            return {}
        conn = db.get_connection()
        self.ensure_schema(conn)
        req = conn.execute('SELECT * FROM approval_requests WHERE id=?', (int(approval_request_id),)).fetchone()
        steps = [dict(r) for r in conn.execute('SELECT * FROM approval_steps WHERE approval_request_id=? ORDER BY step_order', (int(approval_request_id),)).fetchall()]
        return {'request': dict(req) if req else None, 'steps': steps}


advanced_approval_service = AdvancedApprovalService()
