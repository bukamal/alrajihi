# -*- coding: utf-8 -*-
"""Local accounting gateway adapter. Contains SQLite accounting persistence behind gateway boundary."""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Any, Dict
from core.services.audit_service import audit_service
from core.services.rbac_service import rbac_service
from core.services.permission_service import permission_service

class LocalAccountingGateway:
    def is_remote(self) -> bool:
        return False

    DEFAULT_ACCOUNTS = [('1000','Cash / صندوق','ASSET'),('1100','Accounts Receivable / ذمم العملاء','ASSET'),('1200','Inventory / مخزون','ASSET'),('2000','Accounts Payable / ذمم الموردين','LIABILITY'),('3000','Owner Equity / حقوق الملكية','EQUITY'),('3100','Retained Earnings / أرباح مرحلة','EQUITY'),('3900','Current Year Earnings / أرباح السنة الحالية','EQUITY'),('4000','Sales Revenue / إيرادات المبيعات','REVENUE'),('5000','Purchases / مشتريات','EXPENSE'),('5900','Closing Summary / ملخص الإقفال','EQUITY')]
    def _db(self):
        from database.connection import DatabaseConnection
        return DatabaseConnection()
    def _decimal(self, value: Any) -> Decimal:
        try: return Decimal(str(value or '0'))
        except (InvalidOperation, ValueError): return Decimal('0')
    def ensure_schema(self, conn=None) -> None:
        owns = conn is None
        if owns:
            db=self._db()
            if db.is_remote(): return
            conn=db.get_connection()
        conn.execute("""CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, type TEXT NOT NULL, parent_id INTEGER, is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS journal_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, entry_no TEXT UNIQUE, entry_date TEXT NOT NULL, source_type TEXT, source_id INTEGER, description TEXT, status TEXT DEFAULT 'POSTED', created_by TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(source_type, source_id))""")
        conn.execute("""CREATE TABLE IF NOT EXISTS journal_lines (id INTEGER PRIMARY KEY AUTOINCREMENT, journal_entry_id INTEGER NOT NULL, account_id INTEGER NOT NULL, debit TEXT DEFAULT '0', credit TEXT DEFAULT '0', memo TEXT, FOREIGN KEY(journal_entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE, FOREIGN KEY(account_id) REFERENCES accounts(id))""")
        conn.execute('CREATE INDEX IF NOT EXISTS idx_journal_entries_source ON journal_entries(source_type, source_id)')
        conn.execute("""CREATE TABLE IF NOT EXISTS accounting_periods (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL, status TEXT DEFAULT 'OPEN', closed_at TEXT, closed_by TEXT, closing_entry_id INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute('CREATE INDEX IF NOT EXISTS idx_accounting_periods_dates ON accounting_periods(start_date, end_date, status)')
        for code,name,typ in self.DEFAULT_ACCOUNTS: conn.execute('INSERT OR IGNORE INTO accounts(code,name,type) VALUES (?,?,?)',(code,name,typ))
        if owns: conn.commit()
    def _account_id(self, conn, code):
        row=conn.execute('SELECT id FROM accounts WHERE code=?',(code,)).fetchone()
        if not row: raise ValueError(f'الحساب الافتراضي غير موجود: {code}')
        return int(row['id'] if hasattr(row,'keys') else row[0])
    def _next_entry_no(self, conn):
        n=conn.execute('SELECT COALESCE(MAX(id),0)+1 FROM journal_entries').fetchone()[0]
        return f'JE-{int(n):06d}'
    def post_invoice(self, invoice: Dict[str, Any], notes: str = ''):
        try:
            if rbac_service.list_roles() and not rbac_service.has_permission('accounting.post'):
                permission_service.log_event('ACCOUNTING_DENIED', action='accounting.post', allowed=False, reason='rbac_permission_missing', context=str((invoice or {}).get('id')))
                raise PermissionError('لا تملك صلاحية الترحيل المحاسبي حسب RBAC.')
        except PermissionError:
            raise
        except Exception:
            pass
        if not invoice or not invoice.get('id'): return None
        db=self._db()
        if db.is_remote(): return None
        conn=db.get_connection(); self.ensure_schema(conn)
        existing=conn.execute("SELECT id FROM journal_entries WHERE source_type='INVOICE' AND source_id=?",(invoice['id'],)).fetchone()
        if existing: return int(existing['id'] if hasattr(existing,'keys') else existing[0])
        total=self._decimal(invoice.get('total')); paid=self._decimal(invoice.get('paid')); unpaid=total-paid
        if total <= 0: return None
        now=datetime.now().isoformat(timespec='seconds')
        cur=conn.execute("INSERT INTO journal_entries(entry_no, entry_date, source_type, source_id, description, status, created_at) VALUES (?, ?, 'INVOICE', ?, ?, 'POSTED', ?)",(self._next_entry_no(conn), invoice.get('date') or now[:10], invoice['id'], notes or f"Posting invoice {invoice.get('reference','')}", now))
        je_id=int(cur.lastrowid); lines=[]
        if invoice.get('type')=='sale':
            if paid>0: lines.append(('1000',paid,Decimal('0'),'قبض من فاتورة بيع'))
            if unpaid>0: lines.append(('1100',unpaid,Decimal('0'),'ذمم عميل من فاتورة بيع'))
            lines.append(('4000',Decimal('0'),total,'إيراد فاتورة بيع'))
        elif invoice.get('type')=='purchase':
            lines.append(('5000',total,Decimal('0'),'مشتريات من فاتورة شراء'))
            if paid>0: lines.append(('1000',Decimal('0'),paid,'دفع فاتورة شراء'))
            if unpaid>0: lines.append(('2000',Decimal('0'),unpaid,'ذمم مورد من فاتورة شراء'))
        else: return None
        if sum(d for _,d,_,_ in lines) != sum(c for _,_,c,_ in lines): raise ValueError('القيد المحاسبي غير متوازن')
        for code,debit,credit,memo in lines: conn.execute('INSERT INTO journal_lines(journal_entry_id, account_id, debit, credit, memo) VALUES (?,?,?,?,?)',(je_id,self._account_id(conn,code),str(debit),str(credit),memo))
        conn.commit(); audit_service.log('POST_ACCOUNTING','JOURNAL_ENTRY',je_id,new_values={'source_type':'INVOICE','source_id':invoice['id']},details=notes or 'ترحيل محاسبي للفاتورة')
        return je_id
    def trial_balance(self):
        """Return trial balance from real journal lines, not legacy invoice summaries."""
        db = self._db()
        if db.is_remote():
            try:
                return db.get_rest_client().get_accounting_trial_balance()
            except Exception:
                return []
        conn = db.get_connection(); self.ensure_schema(conn)
        rows = conn.execute("""
            SELECT a.id AS account_id, a.code, a.name, a.type,
                   COALESCE(SUM(CAST(jl.debit AS REAL)), 0) AS debit,
                   COALESCE(SUM(CAST(jl.credit AS REAL)), 0) AS credit
            FROM accounts a
            LEFT JOIN journal_lines jl ON jl.account_id = a.id
            LEFT JOIN journal_entries je ON je.id = jl.journal_entry_id AND COALESCE(je.status, 'POSTED') <> 'VOID'
            WHERE COALESCE(a.is_active, 1)=1
            GROUP BY a.id, a.code, a.name, a.type
            ORDER BY a.code
        """).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            debit = self._decimal(d.get('debit'))
            credit = self._decimal(d.get('credit'))
            d['debit'] = str(debit)
            d['credit'] = str(credit)
            d['balance'] = str(debit - credit)
            result.append(d)
        return result

    def ledger(self, account_id=None, start_date=None, end_date=None, limit=1000):
        """Return account ledger rows from journal entries/lines."""
        db = self._db()
        if db.is_remote():
            try:
                return db.get_rest_client().get_accounting_ledger(account_id=account_id, start_date=start_date, end_date=end_date, limit=limit)
            except Exception:
                return []
        conn = db.get_connection(); self.ensure_schema(conn)
        sql = """
            SELECT je.entry_no, je.entry_date, je.source_type, je.source_id, je.description,
                   a.id AS account_id, a.code, a.name AS account_name,
                   CAST(jl.debit AS TEXT) AS debit, CAST(jl.credit AS TEXT) AS credit, jl.memo
            FROM journal_lines jl
            JOIN journal_entries je ON je.id = jl.journal_entry_id
            JOIN accounts a ON a.id = jl.account_id
            WHERE COALESCE(je.status, 'POSTED') <> 'VOID'
        """
        params=[]
        if account_id:
            sql += ' AND a.id=?'
            params.append(account_id)
        if start_date:
            sql += ' AND je.entry_date>=?'
            params.append(start_date)
        if end_date:
            sql += ' AND je.entry_date<=?'
            params.append(end_date)
        sql += ' ORDER BY je.entry_date, je.id, jl.id LIMIT ?'
        params.append(int(limit or 1000))
        rows=[dict(r) for r in conn.execute(sql, tuple(params)).fetchall()]
        running = Decimal('0')
        for r in rows:
            running += self._decimal(r.get('debit')) - self._decimal(r.get('credit'))
            r['balance'] = str(running)
        return rows

    def journal_entries(self, limit=500):
        db = self._db()
        if db.is_remote():
            return []
        conn = db.get_connection(); self.ensure_schema(conn)
        return [dict(r) for r in conn.execute('SELECT * FROM journal_entries ORDER BY id DESC LIMIT ?', (int(limit or 500),)).fetchall()]

    def diagnostics(self):
        db=self._db()
        if db.is_remote(): return {'mode':'remote'}
        conn=db.get_connection(); self.ensure_schema(conn)
        s=lambda q:int(conn.execute(q).fetchone()[0])
        return {'accounts':s('SELECT COUNT(*) FROM accounts'),'journal_entries':s('SELECT COUNT(*) FROM journal_entries'),'unposted_posted_invoices':s("SELECT COUNT(*) FROM invoices i WHERE COALESCE(i.workflow_status,'DRAFT')='POSTED' AND i.deleted_at IS NULL AND NOT EXISTS (SELECT 1 FROM journal_entries j WHERE j.source_type='INVOICE' AND j.source_id=i.id)")}

    def _account_rows_with_balances(self, start_date=None, end_date=None):
        db = self._db()
        if db.is_remote(): return []
        conn = db.get_connection(); self.ensure_schema(conn)
        join_filter = "AND COALESCE(je.status, 'POSTED') <> 'VOID'"
        params = []
        if start_date:
            join_filter += " AND je.entry_date >= ?"; params.append(start_date)
        if end_date:
            join_filter += " AND je.entry_date <= ?"; params.append(end_date)
        sql = f"""
            SELECT a.id AS account_id, a.code, a.name, a.type,
                   COALESCE(SUM(CAST(jl.debit AS REAL)), 0) AS debit,
                   COALESCE(SUM(CAST(jl.credit AS REAL)), 0) AS credit
            FROM accounts a
            LEFT JOIN journal_lines jl ON jl.account_id = a.id
            LEFT JOIN journal_entries je ON je.id = jl.journal_entry_id {join_filter}
            WHERE COALESCE(a.is_active, 1)=1
            GROUP BY a.id, a.code, a.name, a.type
            ORDER BY a.code
        """
        result=[]
        for r in conn.execute(sql, tuple(params)).fetchall():
            d=dict(r); debit=self._decimal(d.get('debit')); credit=self._decimal(d.get('credit'))
            # Natural balance: assets/expenses debit-positive; liabilities/equity/revenue credit-positive.
            typ=(d.get('type') or '').upper()
            natural = debit-credit if typ in ('ASSET','EXPENSE') else credit-debit
            d.update({'debit':str(debit),'credit':str(credit),'balance':str(debit-credit),'natural_balance':str(natural)})
            result.append(d)
        return result

    def income_statement(self, start_date=None, end_date=None):
        """Profit and loss from posted journal lines."""
        db = self._db()
        if db.is_remote():
            try: return db.get_rest_client().get_accounting_income_statement(start_date=start_date, end_date=end_date)
            except Exception: return {'revenues': [], 'expenses': [], 'total_revenue': '0', 'total_expense': '0', 'net_income': '0'}
        rows = self._account_rows_with_balances(start_date, end_date)
        revenues=[r for r in rows if (r.get('type') or '').upper()=='REVENUE' and self._decimal(r.get('natural_balance')) != 0]
        expenses=[r for r in rows if (r.get('type') or '').upper()=='EXPENSE' and self._decimal(r.get('natural_balance')) != 0]
        total_revenue=sum((self._decimal(r.get('natural_balance')) for r in revenues), Decimal('0'))
        total_expense=sum((self._decimal(r.get('natural_balance')) for r in expenses), Decimal('0'))
        return {'revenues': revenues, 'expenses': expenses, 'total_revenue': str(total_revenue), 'total_expense': str(total_expense), 'net_income': str(total_revenue-total_expense), 'start_date': start_date, 'end_date': end_date}

    def balance_sheet(self, as_of_date=None):
        """Balance sheet from posted journal lines up to as_of_date."""
        db = self._db()
        if db.is_remote():
            try: return db.get_rest_client().get_accounting_balance_sheet(as_of_date=as_of_date)
            except Exception: return {'assets': [], 'liabilities': [], 'equity': [], 'balanced': False}
        rows = self._account_rows_with_balances(None, as_of_date)
        assets=[r for r in rows if (r.get('type') or '').upper()=='ASSET' and self._decimal(r.get('natural_balance')) != 0]
        liabilities=[r for r in rows if (r.get('type') or '').upper()=='LIABILITY' and self._decimal(r.get('natural_balance')) != 0]
        equity=[r for r in rows if (r.get('type') or '').upper()=='EQUITY' and self._decimal(r.get('natural_balance')) != 0]
        income=self.income_statement(end_date=as_of_date)
        net_income=self._decimal(income.get('net_income'))
        if net_income != 0:
            equity.append({'account_id': None, 'code': '3900', 'name': 'Current Year Earnings / أرباح السنة الحالية', 'type': 'EQUITY', 'natural_balance': str(net_income), 'debit': '0', 'credit': str(net_income), 'balance': str(-net_income)})
        total_assets=sum((self._decimal(r.get('natural_balance')) for r in assets), Decimal('0'))
        total_liabilities=sum((self._decimal(r.get('natural_balance')) for r in liabilities), Decimal('0'))
        total_equity=sum((self._decimal(r.get('natural_balance')) for r in equity), Decimal('0'))
        return {'assets': assets, 'liabilities': liabilities, 'equity': equity, 'total_assets': str(total_assets), 'total_liabilities': str(total_liabilities), 'total_equity': str(total_equity), 'balanced': total_assets == total_liabilities + total_equity, 'as_of_date': as_of_date}

    def cash_flow(self, start_date=None, end_date=None):
        """Basic cash movement report using cash account 1000."""
        db = self._db()
        if db.is_remote():
            try: return db.get_rest_client().get_accounting_cash_flow(start_date=start_date, end_date=end_date)
            except Exception: return {'rows': [], 'net_cash_flow': '0'}
        rows = self.ledger(account_id=self._account_id(self._db().get_connection(), '1000'), start_date=start_date, end_date=end_date, limit=5000)
        inflow=Decimal('0'); outflow=Decimal('0')
        for r in rows:
            inflow += self._decimal(r.get('debit')); outflow += self._decimal(r.get('credit'))
        return {'rows': rows, 'cash_inflow': str(inflow), 'cash_outflow': str(outflow), 'net_cash_flow': str(inflow-outflow), 'start_date': start_date, 'end_date': end_date}

    def create_opening_balance(self, account_code: str, amount, as_of_date: str, memo: str = ''):
        """Create a balanced opening balance entry against Owner Equity."""
        db=self._db()
        if db.is_remote(): return None
        conn=db.get_connection(); self.ensure_schema(conn)
        amount=self._decimal(amount)
        if amount == 0: return None
        acc_id=self._account_id(conn, account_code); equity_id=self._account_id(conn, '3000')
        account=conn.execute('SELECT type FROM accounts WHERE code=?',(account_code,)).fetchone()
        typ=(account['type'] if hasattr(account,'keys') else account[0]).upper()
        now=datetime.now().isoformat(timespec='seconds')
        cur=conn.execute("INSERT INTO journal_entries(entry_no, entry_date, source_type, source_id, description, status, created_at) VALUES (?, ?, 'OPENING', NULL, ?, 'POSTED', ?)", (self._next_entry_no(conn), as_of_date, memo or f'Opening balance {account_code}', now))
        je_id=int(cur.lastrowid)
        # Positive assets/expenses debit; positive liabilities/equity/revenue credit.
        if typ in ('ASSET','EXPENSE'):
            lines=[(acc_id, amount, Decimal('0')), (equity_id, Decimal('0'), amount)]
        else:
            lines=[(equity_id, amount, Decimal('0')), (acc_id, Decimal('0'), amount)]
        for aid,d,c in lines:
            conn.execute('INSERT INTO journal_lines(journal_entry_id, account_id, debit, credit, memo) VALUES (?,?,?,?,?)',(je_id, aid, str(d), str(c), memo or 'Opening balance'))
        conn.commit(); audit_service.log('OPENING_BALANCE','JOURNAL_ENTRY',je_id,new_values={'account_code':account_code,'amount':str(amount)},details=memo or 'رصيد افتتاحي')
        return je_id

    def close_period(self, name: str, start_date: str, end_date: str, closed_by: str = ''):
        try:
            if rbac_service.list_roles() and not rbac_service.has_permission('accounting.close_period'):
                permission_service.log_event('ACCOUNTING_DENIED', action='accounting.close_period', allowed=False, reason='rbac_permission_missing', context=f'{start_date}..{end_date}')
                raise PermissionError('لا تملك صلاحية إقفال الفترات حسب RBAC.')
        except PermissionError:
            raise
        except Exception:
            pass
        """Close revenue/expense accounts to retained earnings for the period."""
        db=self._db()
        if db.is_remote(): return None
        conn=db.get_connection(); self.ensure_schema(conn)
        existing=conn.execute('SELECT id FROM accounting_periods WHERE start_date=? AND end_date=? AND status=?',(start_date,end_date,'CLOSED')).fetchone()
        if existing: return int(existing['id'] if hasattr(existing,'keys') else existing[0])
        income=self.income_statement(start_date, end_date); net=self._decimal(income.get('net_income'))
        now=datetime.now().isoformat(timespec='seconds')
        cur=conn.execute("INSERT INTO journal_entries(entry_no, entry_date, source_type, source_id, description, status, created_at, created_by) VALUES (?, ?, 'PERIOD_CLOSE', NULL, ?, 'POSTED', ?, ?)", (self._next_entry_no(conn), end_date, f'Period closing {name}', now, closed_by or 'system'))
        je_id=int(cur.lastrowid)
        # Zero out revenue and expense accounts for the period totals, offset retained earnings.
        total_dr=Decimal('0'); total_cr=Decimal('0')
        for r in income.get('revenues', []):
            amt=self._decimal(r.get('natural_balance'))
            if amt:
                conn.execute('INSERT INTO journal_lines(journal_entry_id, account_id, debit, credit, memo) VALUES (?,?,?,?,?)',(je_id, r['account_id'], str(amt), '0', 'Close revenue'))
                total_dr += amt
        for r in income.get('expenses', []):
            amt=self._decimal(r.get('natural_balance'))
            if amt:
                conn.execute('INSERT INTO journal_lines(journal_entry_id, account_id, debit, credit, memo) VALUES (?,?,?,?,?)',(je_id, r['account_id'], '0', str(amt), 'Close expense'))
                total_cr += amt
        re_id=self._account_id(conn,'3100')
        diff=total_dr-total_cr
        if diff>0:
            conn.execute('INSERT INTO journal_lines(journal_entry_id, account_id, debit, credit, memo) VALUES (?,?,?,?,?)',(je_id, re_id, '0', str(diff), 'Transfer net income to retained earnings'))
        elif diff<0:
            conn.execute('INSERT INTO journal_lines(journal_entry_id, account_id, debit, credit, memo) VALUES (?,?,?,?,?)',(je_id, re_id, str(-diff), '0', 'Transfer net loss to retained earnings'))
        curp=conn.execute('INSERT INTO accounting_periods(name,start_date,end_date,status,closed_at,closed_by,closing_entry_id) VALUES (?,?,?,?,?,?,?)',(name,start_date,end_date,'CLOSED',now,closed_by or 'system',je_id))
        conn.commit(); audit_service.log('CLOSE_PERIOD','ACCOUNTING_PERIOD',int(curp.lastrowid),new_values={'start_date':start_date,'end_date':end_date,'closing_entry_id':je_id},details=f'إقفال الفترة {name}')
        return int(curp.lastrowid)

    def periods(self):
        db=self._db()
        if db.is_remote(): return []
        conn=db.get_connection(); self.ensure_schema(conn)
        return [dict(r) for r in conn.execute('SELECT * FROM accounting_periods ORDER BY end_date DESC, id DESC').fetchall()]


# ---------------- Phase156: Receivables / Payables and Aging ----------------
def _phase156_parse_date(value):
    from datetime import date, datetime
    if not value:
        return None
    s = str(value)[:10]
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None

def _phase156_bucket(age_days: int, amount: Decimal) -> dict:
    buckets = {'current': Decimal('0'), 'days_1_30': Decimal('0'), 'days_31_60': Decimal('0'), 'days_61_90': Decimal('0'), 'over_90': Decimal('0')}
    if age_days <= 0:
        buckets['current'] = amount
    elif age_days <= 30:
        buckets['days_1_30'] = amount
    elif age_days <= 60:
        buckets['days_31_60'] = amount
    elif age_days <= 90:
        buckets['days_61_90'] = amount
    else:
        buckets['over_90'] = amount
    return {k: str(v) for k, v in buckets.items()}

def _phase156_party_aging(self, party: str, as_of_date=None):
    """Real AR/AP aging based on unpaid invoice balances.

    party='customer' reads sale invoices and customers.
    party='supplier' reads purchase invoices and suppliers.
    """
    db = self._db()
    if db.is_remote():
        try:
            rc = db.get_rest_client()
            return rc.get_accounting_receivables_aging(as_of_date) if party == 'customer' else rc.get_accounting_payables_aging(as_of_date)
        except Exception:
            return []
    conn = db.get_connection(); self.ensure_schema(conn)
    from datetime import date
    as_of = _phase156_parse_date(as_of_date) or date.today()
    if party == 'customer':
        join_table, id_col, type_value = 'customers', 'customer_id', 'sale'
        name_expr = "COALESCE(p.name, '')"
    else:
        join_table, id_col, type_value = 'suppliers', 'supplier_id', 'purchase'
        name_expr = "COALESCE(p.name, '')"
    sql = f"""
        SELECT p.id AS party_id, {name_expr} AS party_name,
               i.id AS invoice_id, i.reference, i.date, COALESCE(i.due_date, i.date) AS due_date,
               CAST(i.total AS TEXT) AS total, CAST(i.paid AS TEXT) AS paid,
               (CAST(i.total AS REAL) - CAST(COALESCE(i.paid,'0') AS REAL)) AS balance
        FROM invoices i
        LEFT JOIN {join_table} p ON p.id = i.{id_col}
        WHERE i.type=? AND i.{id_col} IS NOT NULL AND i.deleted_at IS NULL
          AND (CAST(i.total AS REAL) - CAST(COALESCE(i.paid,'0') AS REAL)) > 0.000001
        ORDER BY p.name, COALESCE(i.due_date, i.date), i.id
    """
    rows = []
    for r in conn.execute(sql, (type_value,)).fetchall():
        d = dict(r)
        due = _phase156_parse_date(d.get('due_date')) or _phase156_parse_date(d.get('date')) or as_of
        age = max((as_of - due).days, 0)
        bal = self._decimal(d.get('balance'))
        d['age_days'] = age
        d['balance'] = str(bal)
        d.update(_phase156_bucket(age, bal))
        rows.append(d)
    return rows

def _phase156_aging_summary(self, party: str, as_of_date=None):
    rows = _phase156_party_aging(self, party, as_of_date)
    totals = {'current': Decimal('0'), 'days_1_30': Decimal('0'), 'days_31_60': Decimal('0'), 'days_61_90': Decimal('0'), 'over_90': Decimal('0'), 'total': Decimal('0')}
    by_party = {}
    for r in rows:
        key = r.get('party_id')
        rec = by_party.setdefault(key, {'party_id': key, 'party_name': r.get('party_name') or '', 'current': Decimal('0'), 'days_1_30': Decimal('0'), 'days_31_60': Decimal('0'), 'days_61_90': Decimal('0'), 'over_90': Decimal('0'), 'total': Decimal('0')})
        bal = self._decimal(r.get('balance'))
        rec['total'] += bal; totals['total'] += bal
        for bucket in ['current', 'days_1_30', 'days_31_60', 'days_61_90', 'over_90']:
            amount = self._decimal(r.get(bucket))
            rec[bucket] += amount; totals[bucket] += amount
    packed=[]
    for rec in by_party.values():
        packed.append({k: (str(v) if isinstance(v, Decimal) else v) for k,v in rec.items()})
    return {'rows': rows, 'summary': packed, 'totals': {k: str(v) for k,v in totals.items()}, 'as_of_date': str(as_of_date or '')}

def _phase156_receivables_aging(self, as_of_date=None):
    return _phase156_aging_summary(self, 'customer', as_of_date)

def _phase156_payables_aging(self, as_of_date=None):
    return _phase156_aging_summary(self, 'supplier', as_of_date)

def _phase156_party_statement(self, party: str, party_id: int, start_date=None, end_date=None):
    """Operational statement for a customer/supplier from invoices and vouchers.

    Customer: invoice total = debit, receipt voucher/return = credit.
    Supplier: purchase invoice = credit, payment voucher/return = debit.
    """
    db = self._db()
    if db.is_remote():
        try:
            rc = db.get_rest_client()
            return rc.get_accounting_customer_statement(party_id, start_date, end_date) if party == 'customer' else rc.get_accounting_supplier_statement(party_id, start_date, end_date)
        except Exception:
            return {'rows': [], 'balance': '0'}
    conn = db.get_connection(); self.ensure_schema(conn)
    params=[]; rows=[]
    if party == 'customer':
        invoice_where = "type='sale' AND customer_id=? AND deleted_at IS NULL"; params=[party_id]
        voucher_where = "customer_id=?"; voucher_params=[party_id]
        inv_debit, inv_credit = 'total', '0'
        v_debit_case = "CASE WHEN type='refund' THEN CAST(amount AS REAL) ELSE 0 END"
        v_credit_case = "CASE WHEN type IN ('receipt','return','sales_return') THEN CAST(amount AS REAL) ELSE 0 END"
    else:
        invoice_where = "type='purchase' AND supplier_id=? AND deleted_at IS NULL"; params=[party_id]
        voucher_where = "supplier_id=?"; voucher_params=[party_id]
        inv_debit, inv_credit = '0', 'total'
        v_debit_case = "CASE WHEN type IN ('payment','return','purchase_return') THEN CAST(amount AS REAL) ELSE 0 END"
        v_credit_case = "CASE WHEN type='refund' THEN CAST(amount AS REAL) ELSE 0 END"
    date_filter=''
    if start_date:
        date_filter += ' AND date>=?'; params.append(start_date); voucher_params.append(start_date)
    if end_date:
        date_filter += ' AND date<=?'; params.append(end_date); voucher_params.append(end_date)
    for r in conn.execute(f"SELECT date, 'INVOICE' AS source_type, id AS source_id, reference, notes, CAST({inv_debit} AS REAL) AS debit, CAST({inv_credit} AS REAL) AS credit FROM invoices WHERE {invoice_where}{date_filter}", tuple(params)).fetchall():
        rows.append(dict(r))
    for r in conn.execute(f"SELECT date, 'VOUCHER' AS source_type, id AS source_id, reference, description AS notes, {v_debit_case} AS debit, {v_credit_case} AS credit FROM vouchers WHERE {voucher_where}{date_filter}", tuple(voucher_params)).fetchall():
        rows.append(dict(r))
    rows.sort(key=lambda r: (str(r.get('date') or ''), str(r.get('source_type') or ''), int(r.get('source_id') or 0)))
    bal=Decimal('0')
    for r in rows:
        d=self._decimal(r.get('debit')); c=self._decimal(r.get('credit'))
        bal += (d-c) if party == 'customer' else (c-d)
        r['debit']=str(d); r['credit']=str(c); r['balance']=str(bal)
    return {'rows': rows, 'balance': str(bal), 'party_type': party, 'party_id': party_id, 'start_date': start_date, 'end_date': end_date}

def _phase156_customer_statement(self, customer_id: int, start_date=None, end_date=None):
    return _phase156_party_statement(self, 'customer', customer_id, start_date, end_date)

def _phase156_supplier_statement(self, supplier_id: int, start_date=None, end_date=None):
    return _phase156_party_statement(self, 'supplier', supplier_id, start_date, end_date)

LocalAccountingGateway.receivables_aging = _phase156_receivables_aging
LocalAccountingGateway.payables_aging = _phase156_payables_aging
LocalAccountingGateway.customer_statement_accounting = _phase156_customer_statement
LocalAccountingGateway.supplier_statement_accounting = _phase156_supplier_statement
