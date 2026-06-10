# -*- coding: utf-8 -*-
from __future__ import annotations
import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from database.repositories.base_repo import BaseRepository
from auth.session import UserSession
from database.repositories.branch_repo import BranchRepository

DEFAULT_CASHBOX_NAME = 'الصندوق الرئيسي'
DEFAULT_CASHBOX_CODE = 'MAIN-CASH'

class CashboxRepository(BaseRepository):
    def _now(self): return datetime.datetime.now().isoformat()
    def _uid(self): return UserSession.get_current_user_id() or 'admin'

    def ensure_schema(self):
        if self.db.is_remote(): return
        conn = self.db.get_connection(); conn.execute('PRAGMA foreign_keys=ON')
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS cashboxes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            branch_id INTEGER,
            name TEXT NOT NULL,
            code TEXT,
            notes TEXT,
            is_default INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            deleted_at TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (branch_id) REFERENCES branches(id),
            UNIQUE(user_id, branch_id, name),
            UNIQUE(user_id, code)
        );
        CREATE TABLE IF NOT EXISTS bank_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            branch_id INTEGER,
            bank_name TEXT NOT NULL,
            account_name TEXT,
            account_number TEXT,
            iban TEXT,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            deleted_at TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (branch_id) REFERENCES branches(id)
        );
        CREATE TABLE IF NOT EXISTS cash_bank_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            branch_id INTEGER,
            cashbox_id INTEGER,
            bank_account_id INTEGER,
            movement_type TEXT NOT NULL,
            amount TEXT NOT NULL,
            direction TEXT,
            reference_type TEXT,
            reference_id INTEGER,
            description TEXT,
            movement_date TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (branch_id) REFERENCES branches(id),
            FOREIGN KEY (cashbox_id) REFERENCES cashboxes(id),
            FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id)
        );

        CREATE TABLE IF NOT EXISTS pos_shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            branch_id INTEGER,
            cashbox_id INTEGER NOT NULL,
            opening_amount TEXT DEFAULT '0',
            closing_amount TEXT,
            expected_amount TEXT DEFAULT '0',
            actual_amount TEXT,
            difference_amount TEXT,
            total_sales TEXT DEFAULT '0',
            total_cash TEXT DEFAULT '0',
            total_card TEXT DEFAULT '0',
            status TEXT DEFAULT 'open',
            opened_at TEXT,
            closed_at TEXT,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (branch_id) REFERENCES branches(id),
            FOREIGN KEY (cashbox_id) REFERENCES cashboxes(id)
        );
        CREATE INDEX IF NOT EXISTS idx_cashboxes_user_branch ON cashboxes(user_id, branch_id);
        CREATE INDEX IF NOT EXISTS idx_banks_user_branch ON bank_accounts(user_id, branch_id);
        CREATE INDEX IF NOT EXISTS idx_cash_mov_ref ON cash_bank_movements(reference_type, reference_id);
        CREATE INDEX IF NOT EXISTS idx_cash_mov_cashbox ON cash_bank_movements(cashbox_id);
        CREATE INDEX IF NOT EXISTS idx_cash_mov_bank ON cash_bank_movements(bank_account_id);
        CREATE INDEX IF NOT EXISTS idx_pos_shifts_user_status ON pos_shifts(user_id, status);
        CREATE INDEX IF NOT EXISTS idx_pos_shifts_cashbox ON pos_shifts(cashbox_id);
        ''')
        try:
            cols = [r[1] for r in conn.execute('PRAGMA table_info(cash_bank_movements)').fetchall()]
            if 'shift_id' not in cols:
                conn.execute('ALTER TABLE cash_bank_movements ADD COLUMN shift_id INTEGER')
        except Exception:
            pass
        try:
            cols = [r[1] for r in conn.execute('PRAGMA table_info(invoices)').fetchall()]
            for name, typ in [('shift_id','INTEGER'),('cashbox_id','INTEGER'),('bank_account_id','INTEGER'),('payment_method',"TEXT DEFAULT 'cash'")]:
                if name not in cols:
                    conn.execute(f'ALTER TABLE invoices ADD COLUMN {name} {typ}')
        except Exception:
            pass
        for table in ('vouchers','expenses'):

            try:
                cols = [r[1] for r in conn.execute(f'PRAGMA table_info({table})').fetchall()]
                for name, typ in [('cashbox_id','INTEGER'),('bank_account_id','INTEGER'),('payment_method',"TEXT DEFAULT 'cash'")]:
                    if name not in cols:
                        conn.execute(f'ALTER TABLE {table} ADD COLUMN {name} {typ}')
            except Exception:
                pass
        conn.commit()

    def bootstrap_defaults(self):
        if self.db.is_remote(): return
        self.ensure_schema()
        try: BranchRepository().bootstrap_defaults()
        except Exception: pass
        conn = self.db.get_connection(); now = self._now()
        users = conn.execute('''SELECT id FROM users UNION SELECT DISTINCT user_id AS id FROM branches WHERE user_id IS NOT NULL UNION SELECT DISTINCT user_id AS id FROM vouchers WHERE user_id IS NOT NULL''').fetchall()
        for u in users:
            uid = u['id']
            if not uid: continue
            branches = conn.execute('SELECT id FROM branches WHERE user_id=? AND deleted_at IS NULL', (uid,)).fetchall()
            if not branches:
                bid = BranchRepository().default_branch_id(uid)
                branches = [{'id': bid}] if bid else []
            for br in branches:
                bid = br['id']
                if not bid: continue
                row = conn.execute('SELECT id FROM cashboxes WHERE user_id=? AND branch_id=? AND is_default=1 AND deleted_at IS NULL', (uid,bid)).fetchone()
                if row: cid = row['id']
                else:
                    code = f'{DEFAULT_CASHBOX_CODE}-{bid}'
                    cur = conn.execute('''INSERT OR IGNORE INTO cashboxes (user_id, branch_id, name, code, notes, is_default, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 1, 1, ?, ?)''', (uid,bid,DEFAULT_CASHBOX_NAME,code,'تم إنشاؤه تلقائياً عند تفعيل نظام الصناديق',now,now))
                    found = conn.execute('SELECT id FROM cashboxes WHERE user_id=? AND branch_id=? AND name=?', (uid,bid,DEFAULT_CASHBOX_NAME)).fetchone()
                    cid = cur.lastrowid or (found['id'] if found else None)
                if cid:
                    conn.execute("UPDATE vouchers SET cashbox_id=?, payment_method=COALESCE(payment_method,'cash') WHERE user_id=? AND branch_id=? AND cashbox_id IS NULL AND bank_account_id IS NULL", (cid,uid,bid))
        conn.commit(); self.migrate_voucher_movements()

    def default_cashbox_id(self, branch_id=None, user_id=None):
        if self.db.is_remote(): return None
        self.ensure_schema(); uid = user_id or self._uid(); bid = branch_id or BranchRepository().default_branch_id(uid)
        row = self.db.get_connection().execute('SELECT id FROM cashboxes WHERE user_id=? AND branch_id=? AND is_default=1 AND deleted_at IS NULL LIMIT 1', (uid,bid)).fetchone()
        if row: return int(row['id'])
        self.bootstrap_defaults()
        row = self.db.get_connection().execute('SELECT id FROM cashboxes WHERE user_id=? AND branch_id=? AND deleted_at IS NULL ORDER BY is_default DESC, id LIMIT 1', (uid,bid)).fetchone()
        return int(row['id']) if row else None

    def list_cashboxes(self, include_archived=False):
        if self.db.is_remote(): return []
        self.bootstrap_defaults(); uid = self._uid()
        sql = '''SELECT c.*, b.name AS branch_name, COALESCE(SUM(CASE WHEN m.cashbox_id=c.id THEN CAST(m.amount AS REAL) ELSE 0 END),0) AS balance FROM cashboxes c LEFT JOIN branches b ON b.id=c.branch_id LEFT JOIN cash_bank_movements m ON m.cashbox_id=c.id WHERE c.user_id=?'''
        params=[uid]
        if not include_archived: sql += ' AND c.deleted_at IS NULL AND COALESCE(c.is_active,1)=1'
        sql += ' GROUP BY c.id ORDER BY b.name, c.is_default DESC, c.name'
        return [dict(r) for r in self.db.get_connection().execute(sql, params).fetchall()]

    def list_bank_accounts(self, include_archived=False):
        if self.db.is_remote(): return []
        self.bootstrap_defaults(); uid = self._uid()
        sql = '''SELECT ba.*, b.name AS branch_name, COALESCE(SUM(CASE WHEN m.bank_account_id=ba.id THEN CAST(m.amount AS REAL) ELSE 0 END),0) AS balance FROM bank_accounts ba LEFT JOIN branches b ON b.id=ba.branch_id LEFT JOIN cash_bank_movements m ON m.bank_account_id=ba.id WHERE ba.user_id=?'''
        params=[uid]
        if not include_archived: sql += ' AND ba.deleted_at IS NULL AND COALESCE(ba.is_active,1)=1'
        sql += ' GROUP BY ba.id ORDER BY b.name, ba.bank_name, ba.account_name'
        return [dict(r) for r in self.db.get_connection().execute(sql, params).fetchall()]

    def get_cashbox(self, cid):
        row = self.db.get_connection().execute('SELECT * FROM cashboxes WHERE id=? AND user_id=?', (cid,self._uid())).fetchone()
        return dict(row) if row else None
    def get_bank_account(self, bid):
        row = self.db.get_connection().execute('SELECT * FROM bank_accounts WHERE id=? AND user_id=?', (bid,self._uid())).fetchone()
        return dict(row) if row else None

    def add_cashbox(self, data):
        self.bootstrap_defaults(); uid=self._uid(); now=self._now(); p=self._cashbox_payload(data)
        cur=self.db.get_connection().execute('''INSERT INTO cashboxes (user_id, branch_id, name, code, notes, is_default, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)''', (uid,p['branch_id'],p['name'],p['code'],p['notes'],p['is_active'],now,now))
        self.db.get_connection().commit(); return int(cur.lastrowid)
    def update_cashbox(self, cid, data):
        p=self._cashbox_payload(data); conn=self.db.get_connection()
        conn.execute('UPDATE cashboxes SET branch_id=?, name=?, code=?, notes=?, is_active=?, updated_at=? WHERE id=? AND user_id=?', (p['branch_id'],p['name'],p['code'],p['notes'],p['is_active'],self._now(),cid,self._uid()))
        conn.commit()
    def archive_cashbox(self, cid):
        conn=self.db.get_connection(); row=conn.execute('SELECT is_default FROM cashboxes WHERE id=? AND user_id=?',(cid,self._uid())).fetchone()
        if not row: raise ValueError('الصندوق غير موجود')
        if int(row['is_default'] or 0)==1: raise ValueError('لا يمكن أرشفة الصندوق الرئيسي')
        now=self._now(); conn.execute('UPDATE cashboxes SET deleted_at=?, is_active=0, updated_at=? WHERE id=? AND user_id=?',(now,now,cid,self._uid())); conn.commit()

    def add_bank_account(self, data):
        self.bootstrap_defaults(); uid=self._uid(); now=self._now(); p=self._bank_payload(data)
        cur=self.db.get_connection().execute('''INSERT INTO bank_accounts (user_id, branch_id, bank_name, account_name, account_number, iban, notes, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',(uid,p['branch_id'],p['bank_name'],p['account_name'],p['account_number'],p['iban'],p['notes'],p['is_active'],now,now))
        self.db.get_connection().commit(); return int(cur.lastrowid)
    def update_bank_account(self, bid, data):
        p=self._bank_payload(data); conn=self.db.get_connection()
        conn.execute('UPDATE bank_accounts SET branch_id=?, bank_name=?, account_name=?, account_number=?, iban=?, notes=?, is_active=?, updated_at=? WHERE id=? AND user_id=?',(p['branch_id'],p['bank_name'],p['account_name'],p['account_number'],p['iban'],p['notes'],p['is_active'],self._now(),bid,self._uid()))
        conn.commit()
    def archive_bank_account(self, bid):
        now=self._now(); self.db.get_connection().execute('UPDATE bank_accounts SET deleted_at=?, is_active=0, updated_at=? WHERE id=? AND user_id=?',(now,now,bid,self._uid())); self.db.get_connection().commit()

    def record_movement(self, data):
        self.ensure_schema(); uid=self._uid(); now=self._now(); amount=Decimal(str(data.get('amount',0)))
        cur=self.db.get_connection().execute('''INSERT INTO cash_bank_movements (user_id, branch_id, cashbox_id, bank_account_id, movement_type, amount, direction, shift_id, reference_type, reference_id, description, movement_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',(uid,data.get('branch_id'),data.get('cashbox_id'),data.get('bank_account_id'),data['movement_type'],str(amount),data.get('direction'),data.get('shift_id'),data.get('reference_type'),data.get('reference_id'),data.get('description',''),data.get('movement_date') or now,now))
        self.db.get_connection().commit(); return int(cur.lastrowid)
    def movements(self, limit=200, cashbox_id=None, bank_account_id=None):
        self.bootstrap_defaults(); uid=self._uid(); sql='''SELECT m.*, c.name AS cashbox_name, ba.bank_name, ba.account_name, b.name AS branch_name FROM cash_bank_movements m LEFT JOIN cashboxes c ON c.id=m.cashbox_id LEFT JOIN bank_accounts ba ON ba.id=m.bank_account_id LEFT JOIN branches b ON b.id=m.branch_id WHERE m.user_id=?'''; params=[uid]
        if cashbox_id: sql+=' AND m.cashbox_id=?'; params.append(cashbox_id)
        if bank_account_id: sql+=' AND m.bank_account_id=?'; params.append(bank_account_id)
        sql+=' ORDER BY m.id DESC LIMIT ?'; params.append(limit)
        return [dict(r) for r in self.db.get_connection().execute(sql,params).fetchall()]
    def delete_reference_movements(self, reference_type, reference_id):
        self.ensure_schema(); self.db.get_connection().execute('DELETE FROM cash_bank_movements WHERE user_id=? AND reference_type=? AND reference_id=?',(self._uid(),reference_type,reference_id)); self.db.get_connection().commit()

    def migrate_voucher_movements(self):
        self.ensure_schema(); conn=self.db.get_connection(); now=self._now()
        try: rows=conn.execute('SELECT * FROM vouchers WHERE user_id IS NOT NULL').fetchall()
        except Exception: return
        for row in rows:
            v=dict(row); exists=conn.execute("SELECT id FROM cash_bank_movements WHERE reference_type='voucher' AND reference_id=? LIMIT 1",(v['id'],)).fetchone()
            if exists: continue
            amount=Decimal(str(v.get('amount') or 0)); signed=abs(amount) if v.get('type')=='receipt' else -abs(amount); direction='in' if signed>=0 else 'out'
            cashbox_id=v.get('cashbox_id') or self.default_cashbox_id(v.get('branch_id'), v.get('user_id'))
            conn.execute('''INSERT INTO cash_bank_movements (user_id, branch_id, cashbox_id, bank_account_id, movement_type, amount, direction, reference_type, reference_id, description, movement_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'voucher', ?, ?, ?, ?)''',(v['user_id'],v.get('branch_id'),cashbox_id,v.get('bank_account_id'),v.get('type'),str(signed),direction,v['id'],v.get('description') or 'ترحيل سند مالي',v.get('date') or now,now))
        conn.commit()


    def current_open_shift(self, cashbox_id=None):
        self.ensure_schema(); uid=self._uid()
        sql = '''SELECT s.*, c.name AS cashbox_name, b.name AS branch_name FROM pos_shifts s LEFT JOIN cashboxes c ON c.id=s.cashbox_id LEFT JOIN branches b ON b.id=s.branch_id WHERE s.user_id=? AND s.status='open' '''
        params=[uid]
        if cashbox_id:
            sql+=' AND s.cashbox_id=?'; params.append(cashbox_id)
        sql+=' ORDER BY s.id DESC LIMIT 1'
        row=self.db.get_connection().execute(sql,params).fetchone()
        return dict(row) if row else None

    def shifts(self, limit=100, status=None):
        self.ensure_schema(); uid=self._uid()
        sql='''SELECT s.*, c.name AS cashbox_name, b.name AS branch_name FROM pos_shifts s LEFT JOIN cashboxes c ON c.id=s.cashbox_id LEFT JOIN branches b ON b.id=s.branch_id WHERE s.user_id=?'''
        params=[uid]
        if status:
            sql+=' AND s.status=?'; params.append(status)
        sql+=' ORDER BY s.id DESC LIMIT ?'; params.append(limit)
        return [dict(r) for r in self.db.get_connection().execute(sql,params).fetchall()]

    def open_shift(self, data):
        self.ensure_schema(); uid=self._uid(); now=self._now(); branch_id=data.get('branch_id') or BranchRepository().default_branch_id(uid); cashbox_id=data.get('cashbox_id') or self.default_cashbox_id(branch_id, uid)
        if not cashbox_id: raise ValueError('يجب اختيار صندوق للوردية')
        if self.current_open_shift(cashbox_id): raise ValueError('توجد وردية مفتوحة على هذا الصندوق')
        opening=Decimal(str(data.get('opening_amount') or 0))
        cur=self.db.get_connection().execute('''INSERT INTO pos_shifts (user_id, branch_id, cashbox_id, opening_amount, expected_amount, status, opened_at, notes) VALUES (?, ?, ?, ?, ?, 'open', ?, ?)''',(uid,branch_id,cashbox_id,str(opening),str(opening),now,data.get('notes','')))
        self.db.get_connection().commit(); return int(cur.lastrowid)

    def shift_summary(self, shift_id):
        self.ensure_schema(); conn=self.db.get_connection(); uid=self._uid()
        shift=conn.execute('''SELECT s.*, c.name AS cashbox_name, b.name AS branch_name FROM pos_shifts s LEFT JOIN cashboxes c ON c.id=s.cashbox_id LEFT JOIN branches b ON b.id=s.branch_id WHERE s.id=? AND s.user_id=?''',(shift_id,uid)).fetchone()
        if not shift: raise ValueError('الوردية غير موجودة')
        shift=dict(shift)
        rows=conn.execute('SELECT movement_type, amount, direction FROM cash_bank_movements WHERE shift_id=? AND user_id=?',(shift_id,uid)).fetchall()
        total_cash=Decimal('0'); total_card=Decimal('0'); expenses=Decimal('0')
        for r in rows:
            amount=Decimal(str(r['amount'] or 0)); mtype=str(r['movement_type'] or '')
            if mtype in ('pos_sale_cash','sale_cash'):
                total_cash += amount
            elif mtype in ('pos_sale_card','sale_card'):
                total_card += amount
            elif amount < 0:
                expenses += abs(amount)
        opening=Decimal(str(shift.get('opening_amount') or 0))
        expected=opening+total_cash-expenses
        shift.update({'total_cash':str(total_cash),'total_card':str(total_card),'total_sales':str(total_cash+total_card),'expenses':str(expenses),'expected_amount':str(expected)})
        return shift

    def close_shift(self, shift_id, actual_amount, notes=''):
        self.ensure_schema(); conn=self.db.get_connection(); summary=self.shift_summary(shift_id)
        if summary.get('status')!='open': raise ValueError('الوردية مغلقة بالفعل')
        actual=Decimal(str(actual_amount or 0)); expected=Decimal(str(summary.get('expected_amount') or 0)); diff=actual-expected; now=self._now()
        conn.execute('''UPDATE pos_shifts SET closing_amount=?, expected_amount=?, actual_amount=?, difference_amount=?, total_sales=?, total_cash=?, total_card=?, status='closed', closed_at=?, notes=COALESCE(NULLIF(?,''),notes) WHERE id=? AND user_id=?''',(str(actual),str(expected),str(actual),str(diff),summary.get('total_sales','0'),summary.get('total_cash','0'),summary.get('total_card','0'),now,notes,shift_id,self._uid()))
        conn.commit(); return self.shift_summary(shift_id)

    def _cashbox_payload(self, data):
        payload=dict(data or {}); name=str(payload.get('name','')).strip()
        if not name: raise ValueError('اسم الصندوق مطلوب')
        return {'branch_id':payload.get('branch_id') or BranchRepository().default_branch_id(self._uid()), 'name':name, 'code':str(payload.get('code','')).strip().upper(), 'notes':str(payload.get('notes','')).strip(), 'is_active':1 if payload.get('is_active',1) else 0}
    def _bank_payload(self, data):
        payload=dict(data or {}); bank=str(payload.get('bank_name','')).strip()
        if not bank: raise ValueError('اسم البنك مطلوب')
        return {'branch_id':payload.get('branch_id') or BranchRepository().default_branch_id(self._uid()), 'bank_name':bank, 'account_name':str(payload.get('account_name','')).strip(), 'account_number':str(payload.get('account_number','')).strip(), 'iban':str(payload.get('iban','')).strip(), 'notes':str(payload.get('notes','')).strip(), 'is_active':1 if payload.get('is_active',1) else 0}
