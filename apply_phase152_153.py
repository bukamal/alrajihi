from pathlib import Path
import re, textwrap, zipfile, shutil, subprocess, os
root=Path('/mnt/data/phase152_153_work')
services=root/'alrajhi_client/core/services'

(services/'approval_service.py').write_text(r'''# -*- coding: utf-8 -*-
"""Approval Engine foundation (Phase 152).

Provides durable approval requests for invoices. The service is deliberately
small and conservative: it records request/approval/rejection, enforces a
single approval level, and can be extended later to multi-level RBAC without
changing invoice workflow columns.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Any, Dict, Optional

from auth.session import UserSession
from core.services.settings_service import settings_service
from core.services.audit_service import audit_service
from core.services.permission_service import permission_service


class ApprovalService:
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CANCELLED = 'CANCELLED'

    def _db(self):
        from database.connection import DatabaseConnection
        return DatabaseConnection()

    def _decimal(self, value: Any) -> Decimal:
        try:
            return Decimal(str(value or '0'))
        except (InvalidOperation, ValueError):
            return Decimal('0')

    def _threshold(self, inv_type: str) -> Decimal:
        key = 'workflow/sales_approval_threshold' if inv_type == 'sale' else 'workflow/purchase_approval_threshold'
        return self._decimal(settings_service.get(key, '0'))

    def ensure_schema(self, conn=None) -> None:
        owns = conn is None
        if owns:
            db = self._db()
            if db.is_remote():
                return
            conn = db.get_connection()
        conn.execute('''
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
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests(status, entity_type)')
        if owns:
            conn.commit()

    def requires_approval(self, invoice: Dict[str, Any]) -> bool:
        threshold = self._threshold((invoice or {}).get('type'))
        return threshold > 0 and self._decimal((invoice or {}).get('total')) >= threshold

    def ensure_invoice_request(self, invoice: Dict[str, Any], notes: str = '') -> Optional[int]:
        if not invoice or not invoice.get('id') or not self.requires_approval(invoice):
            return None
        db = self._db()
        if db.is_remote():
            return None
        conn = db.get_connection()
        self.ensure_schema(conn)
        now = datetime.now().isoformat(timespec='seconds')
        username = UserSession.get_current_username() or UserSession.get_current_user_id() or ''
        row = conn.execute("SELECT id FROM approval_requests WHERE entity_type='INVOICE' AND entity_id=?", (invoice['id'],)).fetchone()
        if row:
            return int(row['id'])
        cur = conn.execute('''
            INSERT INTO approval_requests(entity_type, entity_id, amount, threshold_amount, status, requested_by, requested_at, created_at, updated_at, decision_notes)
            VALUES ('INVOICE', ?, ?, ?, 'PENDING', ?, ?, ?, ?, ?)
        ''', (invoice['id'], str(invoice.get('total', 0)), str(self._threshold(invoice.get('type'))), username, now, now, now, notes or ''))
        conn.commit()
        audit_service.log('REQUEST_APPROVAL', 'INVOICE', invoice['id'], new_values={'approval_status':'PENDING'}, details=notes or 'طلب اعتماد فاتورة')
        return int(cur.lastrowid)

    def approval_status(self, invoice_id: int) -> str:
        db = self._db()
        if db.is_remote():
            return ''
        conn = db.get_connection()
        self.ensure_schema(conn)
        row = conn.execute("SELECT status FROM approval_requests WHERE entity_type='INVOICE' AND entity_id=?", (invoice_id,)).fetchone()
        return (row['status'] if row else '')

    def assert_can_approve_invoice(self, invoice: Dict[str, Any]) -> None:
        if not invoice:
            raise ValueError('الفاتورة غير موجودة')
        role = (UserSession.get_current_user_role() or 'admin').lower()
        if role != 'admin' and not settings_service.get_bool('approval/non_admin_can_approve', False):
            permission_service.log_event('APPROVAL_DENIED', action='approve_invoice', allowed=False, reason='approval_restricted_to_admin', context=str(invoice.get('id')))
            raise PermissionError('اعتماد الفواتير مسموح للمدير فقط حسب إعدادات الاعتماد.')

    def approve_invoice(self, invoice: Dict[str, Any], notes: str = '') -> None:
        self.assert_can_approve_invoice(invoice)
        if not self.requires_approval(invoice):
            return
        db = self._db()
        if db.is_remote():
            return
        conn = db.get_connection()
        self.ensure_schema(conn)
        self.ensure_invoice_request(invoice, notes)
        now = datetime.now().isoformat(timespec='seconds')
        username = UserSession.get_current_username() or UserSession.get_current_user_id() or ''
        conn.execute('''
            UPDATE approval_requests
            SET status='APPROVED', decided_by=?, decided_at=?, decision_notes=?, updated_at=?
            WHERE entity_type='INVOICE' AND entity_id=?
        ''', (username, now, notes or 'تم اعتماد الفاتورة', now, invoice['id']))
        conn.commit()
        audit_service.log('APPROVE', 'INVOICE_APPROVAL', invoice['id'], new_values={'approval_status':'APPROVED'}, details=notes or 'اعتماد فاتورة')

    def reject_invoice(self, invoice: Dict[str, Any], notes: str = '') -> None:
        if not invoice:
            raise ValueError('الفاتورة غير موجودة')
        db = self._db()
        if db.is_remote():
            return
        conn = db.get_connection()
        self.ensure_schema(conn)
        self.ensure_invoice_request(invoice, notes)
        now = datetime.now().isoformat(timespec='seconds')
        username = UserSession.get_current_username() or UserSession.get_current_user_id() or ''
        conn.execute('''
            UPDATE approval_requests
            SET status='REJECTED', decided_by=?, decided_at=?, decision_notes=?, updated_at=?
            WHERE entity_type='INVOICE' AND entity_id=?
        ''', (username, now, notes or 'رفض الفاتورة', now, invoice['id']))
        conn.commit()
        audit_service.log('REJECT', 'INVOICE_APPROVAL', invoice['id'], new_values={'approval_status':'REJECTED'}, details=notes or 'رفض فاتورة')

    def pending(self, limit: int = 200):
        db = self._db()
        if db.is_remote():
            return []
        conn = db.get_connection()
        self.ensure_schema(conn)
        rows = conn.execute("SELECT * FROM approval_requests WHERE status='PENDING' ORDER BY id DESC LIMIT ?", (int(limit or 200),)).fetchall()
        return [dict(r) for r in rows]

approval_service = ApprovalService()
''', encoding='utf-8')

(services/'accounting_service.py').write_text(r'''# -*- coding: utf-8 -*-
"""Accounting foundation (Phase 153).

Implements a minimal double-entry accounting core: chart of accounts, journal
entries, journal lines, default accounts, and idempotent invoice posting.
"""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Any, Dict

from core.services.audit_service import audit_service


class AccountingService:
    DEFAULT_ACCOUNTS = [
        ('1000', 'Cash / صندوق', 'ASSET'),
        ('1100', 'Accounts Receivable / ذمم العملاء', 'ASSET'),
        ('1200', 'Inventory / مخزون', 'ASSET'),
        ('2000', 'Accounts Payable / ذمم الموردين', 'LIABILITY'),
        ('4000', 'Sales Revenue / إيرادات المبيعات', 'REVENUE'),
        ('5000', 'Purchases / مشتريات', 'EXPENSE'),
    ]

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
        conn.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                parent_id INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_no TEXT UNIQUE,
                entry_date TEXT NOT NULL,
                source_type TEXT,
                source_id INTEGER,
                description TEXT,
                status TEXT DEFAULT 'POSTED',
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_type, source_id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS journal_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_entry_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                debit TEXT DEFAULT '0',
                credit TEXT DEFAULT '0',
                memo TEXT,
                FOREIGN KEY(journal_entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_journal_entries_source ON journal_entries(source_type, source_id)')
        for code, name, typ in self.DEFAULT_ACCOUNTS:
            conn.execute('INSERT OR IGNORE INTO accounts(code, name, type) VALUES (?,?,?)', (code, name, typ))
        if owns:
            conn.commit()

    def _account_id(self, conn, code: str) -> int:
        row = conn.execute('SELECT id FROM accounts WHERE code=?', (code,)).fetchone()
        if not row:
            raise ValueError(f'الحساب الافتراضي غير موجود: {code}')
        return int(row['id'] if hasattr(row, 'keys') else row[0])

    def _next_entry_no(self, conn) -> str:
        row = conn.execute('SELECT COALESCE(MAX(id),0)+1 FROM journal_entries').fetchone()
        n = row[0]
        return f'JE-{int(n):06d}'

    def post_invoice(self, invoice: Dict[str, Any], notes: str = '') -> int | None:
        if not invoice or not invoice.get('id'):
            return None
        db = self._db()
        if db.is_remote():
            return None
        conn = db.get_connection()
        self.ensure_schema(conn)
        existing = conn.execute("SELECT id FROM journal_entries WHERE source_type='INVOICE' AND source_id=?", (invoice['id'],)).fetchone()
        if existing:
            return int(existing['id'] if hasattr(existing, 'keys') else existing[0])
        total = self._decimal(invoice.get('total'))
        paid = self._decimal(invoice.get('paid'))
        unpaid = total - paid
        if total <= 0:
            return None
        entry_no = self._next_entry_no(conn)
        now = datetime.now().isoformat(timespec='seconds')
        cur = conn.execute('''
            INSERT INTO journal_entries(entry_no, entry_date, source_type, source_id, description, status, created_at)
            VALUES (?, ?, 'INVOICE', ?, ?, 'POSTED', ?)
        ''', (entry_no, invoice.get('date') or now[:10], invoice['id'], notes or f"Posting invoice {invoice.get('reference','')}", now))
        je_id = int(cur.lastrowid)
        lines = []
        inv_type = invoice.get('type')
        if inv_type == 'sale':
            if paid > 0:
                lines.append(('1000', paid, Decimal('0'), 'قبض من فاتورة بيع'))
            if unpaid > 0:
                lines.append(('1100', unpaid, Decimal('0'), 'ذمم عميل من فاتورة بيع'))
            lines.append(('4000', Decimal('0'), total, 'إيراد فاتورة بيع'))
        elif inv_type == 'purchase':
            lines.append(('5000', total, Decimal('0'), 'مشتريات من فاتورة شراء'))
            if paid > 0:
                lines.append(('1000', Decimal('0'), paid, 'دفع فاتورة شراء'))
            if unpaid > 0:
                lines.append(('2000', Decimal('0'), unpaid, 'ذمم مورد من فاتورة شراء'))
        else:
            return None
        debit_sum = sum(d for _, d, _, _ in lines)
        credit_sum = sum(c for _, _, c, _ in lines)
        if debit_sum != credit_sum:
            raise ValueError(f'القيد غير متوازن: مدين {debit_sum} / دائن {credit_sum}')
        for code, debit, credit, memo in lines:
            conn.execute('''
                INSERT INTO journal_lines(journal_entry_id, account_id, debit, credit, memo)
                VALUES (?, ?, ?, ?, ?)
            ''', (je_id, self._account_id(conn, code), str(debit), str(credit), memo))
        conn.commit()
        audit_service.log('POST_ACCOUNTING', 'JOURNAL_ENTRY', je_id, new_values={'source_type':'INVOICE','source_id':invoice['id']}, details=notes or 'ترحيل محاسبي للفاتورة')
        return je_id

    def diagnostics(self) -> Dict[str, int]:
        db = self._db()
        if db.is_remote():
            return {'mode': 'remote'}
        conn = db.get_connection()
        self.ensure_schema(conn)
        def scalar(sql):
            return int(conn.execute(sql).fetchone()[0])
        return {
            'accounts': scalar('SELECT COUNT(*) FROM accounts'),
            'journal_entries': scalar('SELECT COUNT(*) FROM journal_entries'),
            'unposted_posted_invoices': scalar("""
                SELECT COUNT(*) FROM invoices i
                WHERE COALESCE(i.workflow_status,'DRAFT')='POSTED'
                  AND i.deleted_at IS NULL
                  AND NOT EXISTS (SELECT 1 FROM journal_entries j WHERE j.source_type='INVOICE' AND j.source_id=i.id)
            """),
        }

accounting_service = AccountingService()
''', encoding='utf-8')

# Patch services __init__
init=services/'__init__.py'
text=init.read_text(encoding='utf-8') if init.exists() else ''
if 'approval_service' not in text:
    text += "\ntry:\n    from .approval_service import approval_service, ApprovalService\nexcept Exception:\n    approval_service = None\n"
if 'accounting_service' not in text:
    text += "\ntry:\n    from .accounting_service import accounting_service, AccountingService\nexcept Exception:\n    accounting_service = None\n"
init.write_text(text, encoding='utf-8')

# Patch invoice_service submit/approve/post
p=services/'invoice_service.py'
s=p.read_text(encoding='utf-8')
if 'from core.services.approval_service import approval_service' not in s:
    s=s.replace('from core.services.workflow_policy_service import workflow_policy_service\n', 'from core.services.workflow_policy_service import workflow_policy_service\nfrom core.services.approval_service import approval_service\nfrom core.services.accounting_service import accounting_service\n')
s=s.replace("""    def submit(self, invoice_id: int, notes: str = '') -> str:\n        return workflow_policy_service.transition_invoice(invoice_id, workflow_policy_service.SUBMITTED, 'submit', notes or 'إرسال الفاتورة للاعتماد')\n\n    def approve(self, invoice_id: int, notes: str = '') -> str:\n        return workflow_policy_service.transition_invoice(invoice_id, workflow_policy_service.APPROVED, 'approve', notes or 'اعتماد الفاتورة')\n\n    def post(self, invoice_id: int, notes: str = '') -> str:\n        return workflow_policy_service.transition_invoice(invoice_id, workflow_policy_service.POSTED, 'post', notes or 'ترحيل الفاتورة')\n""", """    def submit(self, invoice_id: int, notes: str = '') -> str:\n        invoice = self.get(invoice_id)\n        if invoice:\n            approval_service.ensure_invoice_request(invoice, notes or 'إرسال الفاتورة للاعتماد')\n        return workflow_policy_service.transition_invoice(invoice_id, workflow_policy_service.SUBMITTED, 'submit', notes or 'إرسال الفاتورة للاعتماد')\n\n    def approve(self, invoice_id: int, notes: str = '') -> str:\n        invoice = self.get(invoice_id)\n        approval_service.approve_invoice(invoice, notes or 'اعتماد الفاتورة')\n        return workflow_policy_service.transition_invoice(invoice_id, workflow_policy_service.APPROVED, 'approve', notes or 'اعتماد الفاتورة')\n\n    def reject(self, invoice_id: int, notes: str = '') -> str:\n        invoice = self.get(invoice_id)\n        approval_service.reject_invoice(invoice, notes or 'رفض الفاتورة')\n        return workflow_policy_service.transition_invoice(invoice_id, workflow_policy_service.CANCELLED, 'reject', notes or 'رفض الفاتورة')\n\n    def post(self, invoice_id: int, notes: str = '') -> str:\n        invoice = self.get(invoice_id)\n        status = (invoice or {}).get('workflow_status', 'DRAFT')\n        if status != workflow_policy_service.APPROVED:\n            raise ValueError('لا يمكن ترحيل الفاتورة محاسبيًا قبل اعتمادها.')\n        new_status = workflow_policy_service.transition_invoice(invoice_id, workflow_policy_service.POSTED, 'post', notes or 'ترحيل الفاتورة')\n        accounting_service.post_invoice(self.get(invoice_id) or invoice, notes or 'قيد تلقائي من ترحيل فاتورة')\n        return new_status\n""")
p.write_text(s, encoding='utf-8')

# Patch migrations by adding idempotent function snippets into ensure_db and init after workflow block
accounting_sql = r'''
        # Phase152/153 approval + accounting foundation tables
        cursor.executescript('''
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
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT,
                UNIQUE(entity_type, entity_id)
            );
            CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests(status, entity_type);
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                parent_id INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_no TEXT UNIQUE,
                entry_date TEXT NOT NULL,
                source_type TEXT,
                source_id INTEGER,
                description TEXT,
                status TEXT DEFAULT 'POSTED',
                created_by TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_type, source_id)
            );
            CREATE TABLE IF NOT EXISTS journal_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_entry_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                debit TEXT DEFAULT '0',
                credit TEXT DEFAULT '0',
                memo TEXT,
                FOREIGN KEY(journal_entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
            );
            CREATE INDEX IF NOT EXISTS idx_journal_entries_source ON journal_entries(source_type, source_id);
            INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1000','Cash / صندوق','ASSET');
            INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1100','Accounts Receivable / ذمم العملاء','ASSET');
            INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1200','Inventory / مخزون','ASSET');
            INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('2000','Accounts Payable / ذمم الموردين','LIABILITY');
            INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('4000','Sales Revenue / إيرادات المبيعات','REVENUE');
            INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('5000','Purchases / مشتريات','EXPENSE');
            INSERT OR IGNORE INTO settings (key, value, category) VALUES ('approval/non_admin_can_approve', 'false', 'approval');
        ''')
'''
for mp in [root/'alrajhi_client/database/migrations.py', root/'alrajhi_server/database/migrations.py']:
    m=mp.read_text(encoding='utf-8')
    if 'Phase152/153 approval + accounting foundation tables' not in m:
        # insert before apply_common_schema in init and before category support in ensure if client, generic after workflow index creation first occurrence
        m=m.replace("        apply_common_schema(conn)\n", accounting_sql+"\n        apply_common_schema(conn)\n", 1)
        # second occurrence if exists (ensure_db after workflow index)
        if "        # Ensure category hierarchy/status support exists" in m:
            m=m.replace("        # Ensure category hierarchy/status support exists", accounting_sql+"\n        # Ensure category hierarchy/status support exists", 1)
        else:
            m=m.replace("        conn.commit()\n", accounting_sql+"\n        conn.commit()\n", 1)
    mp.write_text(m, encoding='utf-8')

# Patch system diagnostics include accounting/approval
sysfile=services/'system_service.py'
if sysfile.exists():
    sy=sysfile.read_text(encoding='utf-8')
    if 'approval_pending_count' not in sy:
        insert="""
            try:
                checks.append({'code': 'approval_pending_count', 'label': 'طلبات اعتماد معلقة', 'value': scalar("SELECT COUNT(*) FROM approval_requests WHERE status='PENDING'")})
                checks.append({'code': 'journal_entries_count', 'label': 'القيود اليومية', 'value': scalar("SELECT COUNT(*) FROM journal_entries")})
                checks.append({'code': 'unposted_accounting_invoices', 'label': 'فواتير مرحلة بلا قيد محاسبي', 'value': scalar("""
                    SELECT COUNT(*) FROM invoices i
                    WHERE COALESCE(i.workflow_status,'DRAFT')='POSTED'
                    AND i.deleted_at IS NULL
                    AND NOT EXISTS (SELECT 1 FROM journal_entries j WHERE j.source_type='INVOICE' AND j.source_id=i.id)
                """)})
            except Exception:
                pass
"""
        sy=sy.replace("            checks.append({'code': 'security_denied_events', 'label': 'عمليات مرفوضة بالصلاحيات', 'value': scalar(\"SELECT COUNT(*) FROM security_events WHERE allowed=0\")})", "            checks.append({'code': 'security_denied_events', 'label': 'عمليات مرفوضة بالصلاحيات', 'value': scalar(\"SELECT COUNT(*) FROM security_events WHERE allowed=0\")})"+insert)
        sysfile.write_text(sy, encoding='utf-8')

# Patch server api invoices helper for approval/accounting on transition action
api=root/'alrajhi_server/api/invoices.py'
a=api.read_text(encoding='utf-8')
if 'def _ensure_approval_accounting_schema' not in a:
    helper=r'''

def _ensure_approval_accounting_schema(db):
    db.executescript('''
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
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            UNIQUE(entity_type, entity_id)
        );
        CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests(status, entity_type);
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            parent_id INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_no TEXT UNIQUE,
            entry_date TEXT NOT NULL,
            source_type TEXT,
            source_id INTEGER,
            description TEXT,
            status TEXT DEFAULT 'POSTED',
            created_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_type, source_id)
        );
        CREATE TABLE IF NOT EXISTS journal_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journal_entry_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            debit TEXT DEFAULT '0',
            credit TEXT DEFAULT '0',
            memo TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_journal_entries_source ON journal_entries(source_type, source_id);
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1000','Cash / صندوق','ASSET');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1100','Accounts Receivable / ذمم العملاء','ASSET');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1200','Inventory / مخزون','ASSET');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('2000','Accounts Payable / ذمم الموردين','LIABILITY');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('4000','Sales Revenue / إيرادات المبيعات','REVENUE');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('5000','Purchases / مشتريات','EXPENSE');
    ''')

def _account_id(db, code):
    row = db.execute('SELECT id FROM accounts WHERE code=?', (code,)).fetchone()
    return row['id'] if row else None

def _ensure_approval_request(db, invoice, user_id, notes=''):
    _ensure_approval_accounting_schema(db)
    threshold = _workflow_threshold(db, invoice.get('type'))
    amount = Decimal(str(invoice.get('total', 0) or 0))
    if threshold <= 0 or amount < threshold:
        return
    now = datetime.datetime.now().isoformat(timespec='seconds')
    db.execute('''INSERT OR IGNORE INTO approval_requests(entity_type, entity_id, amount, threshold_amount, status, requested_by, requested_at, created_at, updated_at, decision_notes)
                  VALUES ('INVOICE', ?, ?, ?, 'PENDING', ?, ?, ?, ?, ?)''', (invoice['id'], str(amount), str(threshold), user_id, now, now, now, notes or ''))

def _approve_request(db, invoice, user_id, notes=''):
    _ensure_approval_request(db, invoice, user_id, notes)
    now = datetime.datetime.now().isoformat(timespec='seconds')
    db.execute("UPDATE approval_requests SET status='APPROVED', decided_by=?, decided_at=?, decision_notes=?, updated_at=? WHERE entity_type='INVOICE' AND entity_id=?", (user_id, now, notes or 'Approved', now, invoice['id']))

def _post_accounting_invoice(db, invoice, user_id, notes=''):
    _ensure_approval_accounting_schema(db)
    existing = db.execute("SELECT id FROM journal_entries WHERE source_type='INVOICE' AND source_id=?", (invoice['id'],)).fetchone()
    if existing:
        return existing['id']
    total = Decimal(str(invoice.get('total', 0) or 0)); paid = Decimal(str(invoice.get('paid', 0) or 0)); unpaid = total - paid
    if total <= 0: return None
    row = db.execute('SELECT COALESCE(MAX(id),0)+1 AS n FROM journal_entries').fetchone(); entry_no = f"JE-{int(row['n']):06d}"
    now = datetime.datetime.now().isoformat(timespec='seconds')
    cur = db.execute("INSERT INTO journal_entries(entry_no, entry_date, source_type, source_id, description, status, created_by, created_at) VALUES (?, ?, 'INVOICE', ?, ?, 'POSTED', ?, ?)", (entry_no, invoice.get('date') or now[:10], invoice['id'], notes or 'Invoice posting', user_id, now))
    je_id = cur.lastrowid
    lines=[]
    if invoice.get('type') == 'sale':
        if paid > 0: lines.append(('1000', paid, Decimal('0'), 'قبض من فاتورة بيع'))
        if unpaid > 0: lines.append(('1100', unpaid, Decimal('0'), 'ذمم عميل'))
        lines.append(('4000', Decimal('0'), total, 'إيراد مبيعات'))
    elif invoice.get('type') == 'purchase':
        lines.append(('5000', total, Decimal('0'), 'مشتريات'))
        if paid > 0: lines.append(('1000', Decimal('0'), paid, 'دفع شراء'))
        if unpaid > 0: lines.append(('2000', Decimal('0'), unpaid, 'ذمم مورد'))
    if sum(x[1] for x in lines) != sum(x[2] for x in lines): raise ValueError('القيد المحاسبي غير متوازن')
    for code, debit, credit, memo in lines:
        db.execute('INSERT INTO journal_lines(journal_entry_id, account_id, debit, credit, memo) VALUES (?,?,?,?,?)', (je_id, _account_id(db, code), str(debit), str(credit), memo))
    return je_id
'''
    a=a.replace("def _ensure_inventory_ledger_table(db):", helper+"\ndef _ensure_inventory_ledger_table(db):")
# inject actions in transition endpoint before update status
if "_approve_request(db, dict(row), user_id, notes)" not in a:
    a=a.replace("    updates = {'workflow_status': new_status}\n", "    if action == 'submit':\n        _ensure_approval_request(db, dict(row), user_id, notes)\n    if action == 'approve':\n        _approve_request(db, dict(row), user_id, notes)\n    if action == 'post' and old_status != 'APPROVED':\n        return jsonify({'error': 'لا يمكن الترحيل قبل الاعتماد'}), 400\n    if action == 'post':\n        _post_accounting_invoice(db, dict(row), user_id, notes)\n    updates = {'workflow_status': new_status}\n")
api.write_text(a, encoding='utf-8')

# write report
(root/'SETTINGS_PHASE152_153_REAL_APPROVAL_ACCOUNTING_REPORT.md').write_text('''# Phase 152/153 Real Implementation Report\n\nتم تطبيق نواة فعلية للجزأين المتبقيين:\n\n## Phase 152 — Approval Engine\n- جدول approval_requests.\n- خدمة ApprovalService.\n- إنشاء طلب اعتماد للفواتير التي تتجاوز threshold.\n- اعتماد ورفض الفاتورة محليًا.\n- منع اعتماد غير المدير إلا إذا سمح الإعداد approval/non_admin_can_approve.\n- ربط submit/approve/reject في InvoiceService.\n\n## Phase 153 — Accounting Foundation\n- جدول accounts.\n- جدول journal_entries.\n- جدول journal_lines.\n- إنشاء حسابات افتراضية.\n- ترحيل فاتورة البيع/الشراء إلى قيد يومية متوازن عند post.\n- منع post قبل APPROVED.\n- idempotent posting: لا ينشئ قيدًا ثانيًا لنفس الفاتورة.\n\n## Server/Client\n- تطبيق الجداول في migrations للعميل والخادم.\n- ربط endpoint workflow في الخادم بالاعتماد والترحيل المحاسبي.\n- إضافة تشخيص أولي لطلبات الاعتماد والقيود والفواتير المرحلة بلا قيد.\n\n## حدود المرحلة\n- هذه نواة محاسبية، وليست نظام محاسبة كامل بعد.\n- لا يوجد Trial Balance UI أو Ledger UI كامل حتى الآن.\n- لا يوجد multi-level approval بعد؛ الموجود single-level approval قابل للتوسيع.\n''', encoding='utf-8')

# compile
res=subprocess.run(['python3','-m','compileall','-q',str(root/'alrajhi_client'),str(root/'alrajhi_server')], text=True, capture_output=True)
print('compile rc', res.returncode)
print(res.stdout[-1000:])
print(res.stderr[-2000:])
if res.returncode!=0:
    raise SystemExit(res.returncode)

# zip
out=Path('/mnt/data/alrajhi_gateway_phase152_153_approval_accounting_foundation.zip')
if out.exists(): out.unlink()
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in root.rglob('*'):
        if p.is_file():
            z.write(p, p.relative_to(root))
print(out)
