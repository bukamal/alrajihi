# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal
from datetime import date, datetime
from database.repositories.reporting_repo import ReportingRepository


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

    def _db_uid(self):
        from database.connection import DatabaseConnection
        from auth.session import UserSession
        return DatabaseConnection(), UserSession.get_current_user_id()

    def _tables(self):
        db, _uid = self._db_uid()
        try:
            return {str(r[0]).lower() for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        except Exception:
            return set()

    def _has_table(self, table):
        return str(table or '').lower() in self._tables()

    def _columns(self, table):
        db, _uid = self._db_uid()
        try:
            return {str(r[1]).lower() for r in db.execute(f"PRAGMA table_info({table})").fetchall()}
        except Exception:
            return set()

    def _safe_sum_table(self, table, expression, where, params=()):
        if not self._has_table(table):
            return Decimal('0')
        db, _uid = self._db_uid()
        try:
            row = db.execute(f"SELECT CAST(COALESCE(SUM({expression}), 0) AS TEXT) FROM {table} WHERE {where}", tuple(params)).fetchone()
            return Decimal(str(row[0] if row and row[0] is not None else '0'))
        except Exception:
            return Decimal('0')

    def _date_predicate(self, column, start_date=None, end_date=None):
        sql = ''
        params = []
        if start_date:
            sql += f" AND date({column}) >= date(?)"
            params.append(start_date)
        if end_date:
            sql += f" AND date({column}) <= date(?)"
            params.append(end_date)
        return sql, tuple(params)

    def _date_filter(self, base_sql, params, date_col, start_date, end_date):
        if start_date:
            base_sql += f" AND {date_col} >= ?"
            params += (start_date,)
        if end_date:
            base_sql += f" AND {date_col} <= ?"
            params += (end_date,)
        return base_sql, params

    def _statement_rows(self, party_type, party_id, start_date=None, end_date=None):
        """Build a running statement from invoices, returns and vouchers.

        Phase 282: every optional source table is included only when it exists.
        Missing returns/vouchers tables must never blank the whole report. The
        running balance includes movements before start_date as an opening row.
        """
        db, uid = self._db_uid()
        if not uid or not party_id:
            return []
        tables = self._tables()
        parts = []

        def add(sql, params, date_col='date'):
            if end_date:
                sql += f" AND date({date_col}) <= date(?)"
                params = tuple(params) + (end_date,)
            parts.append((sql, tuple(params), date_col))

        if party_type == 'customer':
            if 'invoices' in tables:
                add("""SELECT date AS date, reference AS reference, 'sale_invoice' AS source_type, id AS source_id,
                              CAST(total AS TEXT) AS amount, 'sale_invoice' AS description,
                              CAST(total AS TEXT) AS debit, '0' AS credit
                       FROM invoices WHERE customer_id=? AND type='sale' AND user_id=? AND deleted_at IS NULL""", (party_id, uid))
            if 'sales_returns' in tables:
                add("""SELECT date AS date, return_no AS reference, 'sales_return' AS source_type, id AS source_id,
                              CAST(total AS TEXT) AS amount, 'sales_return' AS description,
                              '0' AS debit, CAST(total AS TEXT) AS credit
                       FROM sales_returns WHERE customer_id=? AND user_id=? AND deleted_at IS NULL""", (party_id, uid))
            if 'vouchers' in tables:
                add("""SELECT date AS date, reference AS reference, 'receipt_voucher' AS source_type, id AS source_id,
                              CAST(amount AS TEXT) AS amount, 'receipt_voucher' AS description,
                              '0' AS debit, CAST(amount AS TEXT) AS credit
                       FROM vouchers WHERE customer_id=? AND type IN ('receipt','sales_return','return') AND user_id=?""", (party_id, uid))
            def apply_to_balance(balance, debit, credit):
                return balance + debit - credit
        else:
            if 'invoices' in tables:
                add("""SELECT date AS date, reference AS reference, 'purchase_invoice' AS source_type, id AS source_id,
                              CAST(total AS TEXT) AS amount, 'purchase_invoice' AS description,
                              '0' AS debit, CAST(total AS TEXT) AS credit
                       FROM invoices WHERE supplier_id=? AND type='purchase' AND user_id=? AND deleted_at IS NULL""", (party_id, uid))
            if 'purchase_returns' in tables:
                add("""SELECT date AS date, return_no AS reference, 'purchase_return' AS source_type, id AS source_id,
                              CAST(total AS TEXT) AS amount, 'purchase_return' AS description,
                              CAST(total AS TEXT) AS debit, '0' AS credit
                       FROM purchase_returns WHERE supplier_id=? AND user_id=? AND deleted_at IS NULL""", (party_id, uid))
            if 'vouchers' in tables:
                add("""SELECT date AS date, reference AS reference, 'payment_voucher' AS source_type, id AS source_id,
                              CAST(amount AS TEXT) AS amount, 'payment_voucher' AS description,
                              CAST(amount AS TEXT) AS debit, '0' AS credit
                       FROM vouchers WHERE supplier_id=? AND type IN ('payment','purchase_return','return') AND user_id=?""", (party_id, uid))
            def apply_to_balance(balance, debit, credit):
                return balance + credit - debit

        if not parts:
            return []
        queries = [part[0] for part in parts]
        params = []
        for _sql, p, _date_col in parts:
            params.extend(p)
        rows = db.execute(" UNION ALL ".join(queries) + " ORDER BY date, source_id", tuple(params)).fetchall()
        result = []
        opening = Decimal('0')
        running = Decimal('0')
        start_key = str(start_date)[:10] if start_date else None

        for row in rows:
            d = dict(row)
            debit = Decimal(str(d.get('debit') or '0'))
            credit = Decimal(str(d.get('credit') or '0'))
            row_date = str(d.get('date') or '')[:10]
            if start_key and row_date and row_date < start_key:
                opening = apply_to_balance(opening, debit, credit)
                continue
            if start_key and not result and opening != 0:
                result.append({
                    'date': start_key,
                    'reference': '',
                    'source_type': 'opening_balance',
                    'source_id': 0,
                    'amount': Decimal('0'),
                    'description': 'opening_balance',
                    'debit': Decimal('0'),
                    'credit': Decimal('0'),
                    'balance': opening,
                })
                running = opening
            running = apply_to_balance(running, debit, credit)
            d['debit'] = debit
            d['credit'] = credit
            d['amount'] = Decimal(str(d.get('amount') or '0'))
            d['balance'] = running
            result.append(d)

        if start_key and opening != 0 and not result:
            result.append({
                'date': start_key,
                'reference': '',
                'source_type': 'opening_balance',
                'source_id': 0,
                'amount': Decimal('0'),
                'description': 'opening_balance',
                'debit': Decimal('0'),
                'credit': Decimal('0'),
                'balance': opening,
            })
        return result

    def get_customer_statement(self, customer_id, start_date=None, end_date=None):
        return self._statement_rows('customer', customer_id, start_date, end_date)

    def get_supplier_statement(self, supplier_id, start_date=None, end_date=None):
        return self._statement_rows('supplier', supplier_id, start_date, end_date)

    def _customer_balance(self, customer_id, uid):
        sales = self._safe_sum_table('invoices', 'CAST(total AS REAL)', "customer_id=? AND type='sale' AND user_id=? AND deleted_at IS NULL", (customer_id, uid))
        returns = self._safe_sum_table('sales_returns', 'CAST(total AS REAL)', "customer_id=? AND user_id=? AND deleted_at IS NULL", (customer_id, uid))
        receipts = self._safe_sum_table('vouchers', 'CAST(amount AS REAL)', "customer_id=? AND type IN ('receipt','sales_return','return') AND user_id=?", (customer_id, uid))
        return sales - returns - receipts

    def _supplier_balance(self, supplier_id, uid):
        purchases = self._safe_sum_table('invoices', 'CAST(total AS REAL)', "supplier_id=? AND type='purchase' AND user_id=? AND deleted_at IS NULL", (supplier_id, uid))
        returns = self._safe_sum_table('purchase_returns', 'CAST(total AS REAL)', "supplier_id=? AND user_id=? AND deleted_at IS NULL", (supplier_id, uid))
        payments = self._safe_sum_table('vouchers', 'CAST(amount AS REAL)', "supplier_id=? AND type IN ('payment','purchase_return','return') AND user_id=?", (supplier_id, uid))
        return purchases - returns - payments

    def get_customer_balances(self):
        db, uid = self._db_uid()
        if not uid or not self._has_table('customers'):
            return []
        rows = db.execute("""
            SELECT id, name, phone, address, CAST(COALESCE(balance,0) AS TEXT) AS stored_balance
            FROM customers WHERE user_id=? ORDER BY name
        """, (uid,)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            calc = self._customer_balance(d.get('id'), uid)
            d['balance'] = calc
            d['calculated_balance'] = calc
            result.append(d)
        return result

    def get_supplier_balances(self):
        db, uid = self._db_uid()
        if not uid or not self._has_table('suppliers'):
            return []
        rows = db.execute("""
            SELECT id, name, phone, address, CAST(COALESCE(balance,0) AS TEXT) AS stored_balance
            FROM suppliers WHERE user_id=? ORDER BY name
        """, (uid,)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            calc = self._supplier_balance(d.get('id'), uid)
            d['balance'] = calc
            d['calculated_balance'] = calc
            result.append(d)
        return result

    def _aging(self, table, name_col='name', as_of_date=None):
        db, uid = self._db_uid()
        if not uid:
            return []
        as_of = self._parse_date(as_of_date) or date.today()
        source = self.get_customer_balances() if table == 'customers' else self.get_supplier_balances()
        result = []
        for d in source:
            bal = Decimal(str(d.get('balance') or 0))
            last_date = self._last_party_date(table, d['id'], uid)
            age = (as_of - (self._parse_date(last_date) or as_of)).days
            buckets = {'current': Decimal('0'), 'days_1_30': Decimal('0'), 'days_31_60': Decimal('0'), 'days_61_90': Decimal('0'), 'over_90': Decimal('0')}
            if age <= 0:
                buckets['current'] = bal
            elif age <= 30:
                buckets['days_1_30'] = bal
            elif age <= 60:
                buckets['days_31_60'] = bal
            elif age <= 90:
                buckets['days_61_90'] = bal
            else:
                buckets['over_90'] = bal
            result.append({**d, 'last_transaction_date': last_date or '', 'age_days': max(age, 0), 'total': bal, **buckets})
        return result

    def _last_party_date(self, table, party_id, uid):
        parts = []
        params = []
        if table == 'customers':
            if self._has_table('invoices'):
                parts.append("SELECT date AS dt FROM invoices WHERE customer_id=? AND type='sale' AND user_id=? AND deleted_at IS NULL")
                params.extend([party_id, uid])
            if self._has_table('sales_returns'):
                parts.append("SELECT date AS dt FROM sales_returns WHERE customer_id=? AND user_id=? AND deleted_at IS NULL")
                params.extend([party_id, uid])
            if self._has_table('vouchers'):
                parts.append("SELECT date AS dt FROM vouchers WHERE customer_id=? AND type IN ('receipt','sales_return','return') AND user_id=?")
                params.extend([party_id, uid])
        else:
            if self._has_table('invoices'):
                parts.append("SELECT date AS dt FROM invoices WHERE supplier_id=? AND type='purchase' AND user_id=? AND deleted_at IS NULL")
                params.extend([party_id, uid])
            if self._has_table('purchase_returns'):
                parts.append("SELECT date AS dt FROM purchase_returns WHERE supplier_id=? AND user_id=? AND deleted_at IS NULL")
                params.extend([party_id, uid])
            if self._has_table('vouchers'):
                parts.append("SELECT date AS dt FROM vouchers WHERE supplier_id=? AND type IN ('payment','purchase_return','return') AND user_id=?")
                params.extend([party_id, uid])
        if not parts:
            return None
        return db_execute_scalar("SELECT MAX(dt) FROM (" + " UNION ALL ".join(parts) + ")", tuple(params))

    def get_customer_aging(self, as_of_date=None):
        return self._aging('customers', as_of_date=as_of_date)

    def get_supplier_aging(self, as_of_date=None):
        return self._aging('suppliers', as_of_date=as_of_date)

    def get_trial_balance(self):
        db, uid = self._db_uid()
        if not uid:
            return []
        sales = self._safe_sum("SELECT SUM(CAST(total AS REAL)) FROM invoices WHERE type='sale' AND user_id=? AND deleted_at IS NULL", (uid,))
        sales_returns = self._safe_sum("SELECT SUM(CAST(total AS REAL)) FROM sales_returns WHERE user_id=? AND deleted_at IS NULL", (uid,))
        purchases = self._safe_sum("SELECT SUM(CAST(total AS REAL)) FROM invoices WHERE type='purchase' AND user_id=? AND deleted_at IS NULL", (uid,))
        purchase_returns = self._safe_sum("SELECT SUM(CAST(total AS REAL)) FROM purchase_returns WHERE user_id=? AND deleted_at IS NULL", (uid,))
        expenses = self._safe_sum("SELECT SUM(CAST(amount AS REAL)) FROM expenses WHERE user_id=?", (uid,))
        cash = self._safe_sum("SELECT CAST(cash_balance AS REAL) FROM users WHERE id=?", (uid,))
        receivables = self._safe_sum("SELECT SUM(CAST(balance AS REAL)) FROM customers WHERE user_id=?", (uid,))
        payables = self._safe_sum("SELECT SUM(CAST(balance AS REAL)) FROM suppliers WHERE user_id=?", (uid,))
        return [
            {'name':'الصندوق','debit':cash if cash>0 else Decimal('0'),'credit':-cash if cash<0 else Decimal('0')},
            {'name':'الذمم المدينة','debit':receivables,'credit':Decimal('0')},
            {'name':'الذمم الدائنة','debit':Decimal('0'),'credit':payables},
            {'name':'المبيعات','debit':Decimal('0'),'credit':sales},
            {'name':'مرتجعات المبيعات','debit':sales_returns,'credit':Decimal('0')},
            {'name':'المشتريات','debit':purchases,'credit':Decimal('0')},
            {'name':'مرتجعات المشتريات','debit':Decimal('0'),'credit':purchase_returns},
            {'name':'المصاريف','debit':expenses,'credit':Decimal('0')},
        ]

    def _safe_sum(self, sql, params):
        db, _ = self._db_uid()
        cur = db.execute(sql, params)
        val = cur.fetchone()[0]
        return Decimal(str(val)) if val is not None else Decimal('0')

    def _parse_date(self, value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value)[:10]).date()
        except Exception:
            return None


def db_execute_scalar(sql, params):
    from database.connection import DatabaseConnection
    db = DatabaseConnection()
    row = db.execute(sql, params).fetchone()
    return row[0] if row else None


# Backward-compatible singleton for legacy imports.
reporting_dao = ReportingDAO()


# Keep legacy ``from database.dao import reporting_dao`` imports returning the
# singleton object even after Python has attached the submodule object to the
# package during import.
try:
    import sys
    _dao_pkg = sys.modules.get("database.dao")
    if _dao_pkg is not None:
        setattr(_dao_pkg, "reporting_dao", reporting_dao)
except Exception:
    pass
