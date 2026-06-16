# -*- coding: utf-8 -*-
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Any, Dict, Optional
from auth.session import UserSession
from core.services.settings_service import settings_service
from core.services.audit_service import audit_service
from core.services.permission_service import permission_service
from core.services.rbac_service import rbac_service

class ApprovalService:
    STATUS_PENDING = 'PENDING'; STATUS_APPROVED = 'APPROVED'; STATUS_REJECTED = 'REJECTED'; STATUS_CANCELLED = 'CANCELLED'
    def _db(self):
        from database.connection import DatabaseConnection
        return DatabaseConnection()
    def _decimal(self, value: Any) -> Decimal:
        try: return Decimal(str(value or '0'))
        except (InvalidOperation, ValueError): return Decimal('0')
    def _threshold(self, inv_type: str) -> Decimal:
        key = 'workflow/sales_approval_threshold' if inv_type == 'sale' else 'workflow/purchase_approval_threshold'
        return self._decimal(settings_service.get(key, '0'))
    def ensure_schema(self, conn=None) -> None:
        owns = conn is None
        if owns:
            db = self._db()
            if db.is_remote(): return
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
        if owns: conn.commit()
    def requires_approval(self, invoice: Dict[str, Any]) -> bool:
        threshold = self._threshold((invoice or {}).get('type'))
        return threshold > 0 and self._decimal((invoice or {}).get('total')) >= threshold
    def ensure_invoice_request(self, invoice: Dict[str, Any], notes: str = '') -> Optional[int]:
        if not invoice or not invoice.get('id') or not self.requires_approval(invoice): return None
        db = self._db()
        if db.is_remote(): return None
        conn = db.get_connection(); self.ensure_schema(conn)
        now = datetime.now().isoformat(timespec='seconds')
        username = UserSession.get_current_username() or UserSession.get_current_user_id() or ''
        row = conn.execute("SELECT id FROM approval_requests WHERE entity_type='INVOICE' AND entity_id=?", (invoice['id'],)).fetchone()
        if row: return int(row['id'])
        cur = conn.execute("""
            INSERT INTO approval_requests(entity_type, entity_id, amount, threshold_amount, status, requested_by, requested_at, created_at, updated_at, decision_notes)
            VALUES ('INVOICE', ?, ?, ?, 'PENDING', ?, ?, ?, ?, ?)
        """, (invoice['id'], str(invoice.get('total', 0)), str(self._threshold(invoice.get('type'))), username, now, now, now, notes or ''))
        conn.commit()
        audit_service.log('REQUEST_APPROVAL', 'INVOICE', invoice['id'], new_values={'approval_status':'PENDING'}, details=notes or 'طلب اعتماد فاتورة')
        return int(cur.lastrowid)
    def assert_can_approve_invoice(self, invoice: Dict[str, Any]) -> None:
        if not invoice: raise ValueError('الفاتورة غير موجودة')
        role = (UserSession.get_current_user_role() or 'admin').lower()
        try:
            if rbac_service.list_roles():
                if not rbac_service.has_permission('approval.approve'):
                    permission_service.log_event('APPROVAL_DENIED', action='approval.approve', allowed=False, reason='rbac_permission_missing', context=str(invoice.get('id')))
                    raise PermissionError('لا تملك صلاحية اعتماد الفواتير حسب RBAC.')
                return
        except PermissionError:
            raise
        except Exception:
            pass
        if role != 'admin' and not settings_service.get_bool('approval/non_admin_can_approve', False):
            permission_service.log_event('APPROVAL_DENIED', action='approve_invoice', allowed=False, reason='approval_restricted_to_admin', context=str(invoice.get('id')))
            raise PermissionError('اعتماد الفواتير مسموح للمدير فقط حسب إعدادات الاعتماد.')
    def approve_invoice(self, invoice: Dict[str, Any], notes: str = '') -> None:
        self.assert_can_approve_invoice(invoice)
        if not self.requires_approval(invoice): return
        db = self._db()
        if db.is_remote(): return
        conn = db.get_connection(); self.ensure_schema(conn); self.ensure_invoice_request(invoice, notes)
        now = datetime.now().isoformat(timespec='seconds'); username = UserSession.get_current_username() or UserSession.get_current_user_id() or ''
        conn.execute("""
            UPDATE approval_requests SET status='APPROVED', decided_by=?, decided_at=?, decision_notes=?, updated_at=?
            WHERE entity_type='INVOICE' AND entity_id=?
        """, (username, now, notes or 'تم اعتماد الفاتورة', now, invoice['id']))
        conn.commit(); audit_service.log('APPROVE', 'INVOICE_APPROVAL', invoice['id'], new_values={'approval_status':'APPROVED'}, details=notes or 'اعتماد فاتورة')
    def reject_invoice(self, invoice: Dict[str, Any], notes: str = '') -> None:
        if not invoice: raise ValueError('الفاتورة غير موجودة')
        try:
            if rbac_service.list_roles() and not rbac_service.has_permission('approval.reject'):
                permission_service.log_event('APPROVAL_DENIED', action='approval.reject', allowed=False, reason='rbac_permission_missing', context=str(invoice.get('id')))
                raise PermissionError('لا تملك صلاحية رفض الاعتماد حسب RBAC.')
        except PermissionError:
            raise
        except Exception:
            pass
        db = self._db()
        if db.is_remote(): return
        conn = db.get_connection(); self.ensure_schema(conn); self.ensure_invoice_request(invoice, notes)
        now = datetime.now().isoformat(timespec='seconds'); username = UserSession.get_current_username() or UserSession.get_current_user_id() or ''
        conn.execute("""
            UPDATE approval_requests SET status='REJECTED', decided_by=?, decided_at=?, decision_notes=?, updated_at=?
            WHERE entity_type='INVOICE' AND entity_id=?
        """, (username, now, notes or 'رفض الفاتورة', now, invoice['id']))
        conn.commit(); audit_service.log('REJECT', 'INVOICE_APPROVAL', invoice['id'], new_values={'approval_status':'REJECTED'}, details=notes or 'رفض فاتورة')
    def pending(self, limit: int = 200):
        db = self._db()
        if db.is_remote(): return []
        conn = db.get_connection(); self.ensure_schema(conn)
        return [dict(r) for r in conn.execute("SELECT * FROM approval_requests WHERE status='PENDING' ORDER BY id DESC LIMIT ?", (int(limit or 200),)).fetchall()]

approval_service = ApprovalService()
