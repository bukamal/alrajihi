# -*- coding: utf-8 -*-
"""Workflow policy service (Phase 151).

Centralizes document lifecycle rules for invoices and other future business
objects. The first integration point is invoices because they carry inventory,
financial and return-side effects.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional

from core.services.settings_service import settings_service
from core.services.audit_service import audit_service
from core.services.permission_service import permission_service


class WorkflowPolicyService:
    DRAFT = 'DRAFT'
    SUBMITTED = 'SUBMITTED'
    APPROVED = 'APPROVED'
    POSTED = 'POSTED'
    CANCELLED = 'CANCELLED'

    VALID_STATUSES = {DRAFT, SUBMITTED, APPROVED, POSTED, CANCELLED}

    ACTION_SUBMIT = 'workflow.submit'
    ACTION_APPROVE = 'workflow.approve'
    ACTION_POST = 'workflow.post'
    ACTION_CANCEL = 'workflow.cancel'
    ACTION_REOPEN = 'workflow.reopen'

    DEFAULT_EDIT_POLICY = {
        DRAFT: True,
        SUBMITTED: True,
        APPROVED: False,
        POSTED: False,
        CANCELLED: False,
    }
    DEFAULT_DELETE_POLICY = {
        DRAFT: True,
        SUBMITTED: True,
        APPROVED: False,
        POSTED: False,
        CANCELLED: False,
    }

    def normalize_status(self, status: Any) -> str:
        value = str(status or self.DRAFT).strip().upper()
        return value if value in self.VALID_STATUSES else self.DRAFT

    def _setting_bool(self, key: str, default: bool) -> bool:
        try:
            return settings_service.get_bool(key, default)
        except Exception:
            return default

    def _to_decimal(self, value: Any) -> Decimal:
        try:
            return Decimal(str(value or '0'))
        except (InvalidOperation, ValueError):
            return Decimal('0')

    def threshold_for(self, doc_type: str) -> Decimal:
        key = 'workflow/sales_approval_threshold' if doc_type == 'sale' else 'workflow/purchase_approval_threshold'
        return self._to_decimal(settings_service.get(key, '0'))

    def initial_status(self, doc_type: str, total: Any) -> str:
        """Return initial lifecycle status for a new document.

        A positive approval threshold marks large documents as SUBMITTED so they
        can be discovered by diagnostics/approval screens. Otherwise documents
        remain DRAFT to preserve current editable workflows until explicit
        approval/posting UI is introduced.
        """
        amount = self._to_decimal(total)
        threshold = self.threshold_for(doc_type)
        if threshold > 0 and amount >= threshold:
            return self.SUBMITTED
        return self.DRAFT

    def can_edit_status(self, status: Any) -> bool:
        status = self.normalize_status(status)
        key = f'workflow/allow_edit_{status.lower()}'
        return self._setting_bool(key, self.DEFAULT_EDIT_POLICY.get(status, False))

    def can_delete_status(self, status: Any) -> bool:
        status = self.normalize_status(status)
        key = f'workflow/allow_delete_{status.lower()}'
        return self._setting_bool(key, self.DEFAULT_DELETE_POLICY.get(status, False))

    def assert_can_edit(self, document: Optional[Dict], entity_type: str = 'INVOICE') -> None:
        status = self.normalize_status((document or {}).get('workflow_status') or (document or {}).get('status'))
        if not permission_service.can(permission_service.ACTION_EDIT_INVOICES):
            raise PermissionError(permission_service.denied_message(permission_service.ACTION_EDIT_INVOICES))
        if not self.can_edit_status(status):
            permission_service.log_event('WORKFLOW_DENIED', action='edit', allowed=False,
                                         reason=f'edit_not_allowed_for_{status.lower()}', context=entity_type)
            raise ValueError(f'لا يمكن تعديل المستند في حالة {status}. غيّر سياسة سير العمل أو أعد فتح المستند.')

    def assert_can_delete(self, document: Optional[Dict], entity_type: str = 'INVOICE') -> None:
        status = self.normalize_status((document or {}).get('workflow_status') or (document or {}).get('status'))
        if not permission_service.can(permission_service.ACTION_DELETE):
            raise PermissionError(permission_service.denied_message(permission_service.ACTION_DELETE))
        if not self.can_delete_status(status):
            permission_service.log_event('WORKFLOW_DENIED', action='delete', allowed=False,
                                         reason=f'delete_not_allowed_for_{status.lower()}', context=entity_type)
            raise ValueError(f'لا يمكن حذف المستند في حالة {status}. استخدم الإلغاء أو أعد فتح المستند حسب السياسة.')

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
        try:
            from database.connection import DatabaseConnection
            db = DatabaseConnection()
            if db.is_remote():
                return
            conn = db.get_connection()
            self._ensure_schema(conn)
            conn.commit()
        except Exception:
            pass

    def transition_invoice(self, invoice_id: int, new_status: str, action: str, notes: str = '') -> str:
        from database.connection import DatabaseConnection
        from auth.session import UserSession
        db = DatabaseConnection()
        if db.is_remote():
            result = db.get_rest_client().transition_invoice_workflow(invoice_id, new_status, action, notes)
            if isinstance(result, dict):
                return self.normalize_status(result.get('workflow_status') or new_status)
            return self.normalize_status(new_status)
        conn = db.get_connection()
        self._ensure_schema(conn)
        row = conn.execute('SELECT * FROM invoices WHERE id=? AND deleted_at IS NULL', (invoice_id,)).fetchone()
        if not row:
            raise ValueError('الفاتورة غير موجودة')
        old_status = self.normalize_status(row['workflow_status'] if 'workflow_status' in row.keys() else row['status'])
        new_status = self.normalize_status(new_status)
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
        audit_service.log(action.upper(), 'INVOICE_WORKFLOW', invoice_id,
                          old_values={'workflow_status': old_status},
                          new_values={'workflow_status': new_status}, details=notes or action)
        return new_status

    def diagnostics(self) -> Dict[str, Any]:
        try:
            from database.connection import DatabaseConnection
            db = DatabaseConnection()
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
        except Exception as exc:
            return {'mode': 'error', 'error': str(exc)}


workflow_policy_service = WorkflowPolicyService()
