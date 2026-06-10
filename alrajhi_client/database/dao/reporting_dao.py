# -*- coding: utf-8 -*-
from database.repositories.reporting_repo import ReportingRepository
from decimal import Decimal

class ReportingDAO:
    def __init__(self):
        self.repo = ReportingRepository()
    
    def get_summary(self):
        return self.repo.get_summary_filtered()
    
    def get_summary_filtered(self, start_date=None, end_date=None):
        return self.repo.get_summary_filtered(start_date, end_date)
    
    def get_income_statement(self):
        return self.get_income_statement_filtered()
    
    def get_income_statement_filtered(self, start_date=None, end_date=None):
        return self.repo.get_income_statement_filtered(start_date, end_date)
    
    def get_balance_sheet(self):
        return self.get_balance_sheet_filtered()
    
    def get_balance_sheet_filtered(self, start_date=None, end_date=None):
        return self.repo.get_balance_sheet_filtered(start_date, end_date)
    
    def get_customer_statement(self, customer_id):
        from database.connection import DatabaseConnection
        from auth.session import UserSession
        db = DatabaseConnection()
        uid = UserSession.get_current_user_id()
        rows = db.execute("""
            SELECT date, reference, 
                   CAST(total AS TEXT) as amount, 
                   'فاتورة' as description, 
                   CAST(total AS TEXT) as debit, 
                   '0' as credit
            FROM invoices WHERE customer_id=? AND type='sale' AND user_id=? AND deleted_at IS NULL
            UNION ALL
            SELECT date, reference, 
                   CAST(amount AS TEXT), 
                   'سند قبض', 
                   '0', 
                   CAST(amount AS TEXT)
            FROM vouchers WHERE customer_id=? AND type='receipt' AND user_id=?
            ORDER BY date
        """, (customer_id, uid, customer_id, uid)).fetchall()
        result = []
        balance = Decimal('0')
        for row in rows:
            d = dict(row)
            d['debit'] = Decimal(str(d.get('debit', '0')))
            d['credit'] = Decimal(str(d.get('credit', '0')))
            balance += d['debit'] - d['credit']
            d['balance'] = balance
            result.append(d)
        return result
    
    def get_supplier_statement(self, supplier_id):
        from database.connection import DatabaseConnection
        from auth.session import UserSession
        db = DatabaseConnection()
        uid = UserSession.get_current_user_id()
        rows = db.execute("""
            SELECT date, reference, 
                   CAST(total AS TEXT) as amount, 
                   'فاتورة' as description, 
                   '0' as debit, 
                   CAST(total AS TEXT) as credit
            FROM invoices WHERE supplier_id=? AND type='purchase' AND user_id=? AND deleted_at IS NULL
            UNION ALL
            SELECT date, reference, 
                   CAST(amount AS TEXT), 
                   'سند دفع', 
                   CAST(amount AS TEXT), 
                   '0'
            FROM vouchers WHERE supplier_id=? AND type='payment' AND user_id=?
            ORDER BY date
        """, (supplier_id, uid, supplier_id, uid)).fetchall()
        result = []
        balance = Decimal('0')
        for row in rows:
            d = dict(row)
            d['debit'] = Decimal(str(d.get('debit', '0')))
            d['credit'] = Decimal(str(d.get('credit', '0')))
            balance += d['credit'] - d['debit']
            d['balance'] = balance
            result.append(d)
        return result
    
    def get_trial_balance(self):
        from database.connection import DatabaseConnection
        from auth.session import UserSession
        db = DatabaseConnection()
        uid = UserSession.get_current_user_id()
        sales = self._safe_sum("SELECT SUM(CAST(total AS REAL)) FROM invoices WHERE type='sale' AND user_id=? AND deleted_at IS NULL", (uid,))
        purchases = self._safe_sum("SELECT SUM(CAST(total AS REAL)) FROM invoices WHERE type='purchase' AND user_id=? AND deleted_at IS NULL", (uid,))
        expenses = self._safe_sum("SELECT SUM(CAST(amount AS REAL)) FROM expenses WHERE user_id=?", (uid,))
        cash = self._safe_sum("SELECT CAST(cash_balance AS REAL) FROM users WHERE id=?", (uid,))
        receivables = self._safe_sum("SELECT SUM(CAST(balance AS REAL)) FROM customers WHERE user_id=?", (uid,))
        payables = self._safe_sum("SELECT SUM(CAST(balance AS REAL)) FROM suppliers WHERE user_id=?", (uid,))
        return [
            {'name':'الصندوق','debit':cash if cash>0 else 0,'credit':-cash if cash<0 else 0},
            {'name':'الذمم المدينة','debit':receivables,'credit':0},
            {'name':'الذمم الدائنة','debit':0,'credit':payables},
            {'name':'المبيعات','debit':0,'credit':sales},
            {'name':'المشتريات','debit':purchases,'credit':0},
            {'name':'المصاريف','debit':expenses,'credit':0}
        ]
    
    def _safe_sum(self, sql, params):
        from database.connection import DatabaseConnection
        db = DatabaseConnection()
        cur = db.execute(sql, params)
        val = cur.fetchone()[0]
        return Decimal(str(val)) if val else Decimal('0')


