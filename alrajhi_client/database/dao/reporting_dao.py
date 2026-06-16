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

    def _date_filter(self, base_sql, params, date_col, start_date, end_date):
        if start_date:
            base_sql += f" AND {date_col} >= ?"
            params += (start_date,)
        if end_date:
            base_sql += f" AND {date_col} <= ?"
            params += (end_date,)
        return base_sql, params

    def _statement_rows(self, party_type, party_id, start_date=None, end_date=None):
        """Build a true running account statement for customers/suppliers.

        The running balance must include transactions before ``start_date`` as
        an opening balance, otherwise a date-filtered account statement shows a
        mathematically correct period total but an incorrect current balance.
        This method intentionally keeps all sources in one place so the reports
        UI does not recalculate balances independently.
        """
        db, uid = self._db_uid()
        if not uid or not party_id:
            return []

        if party_type == 'customer':
            parts = [
                ("""SELECT date AS date, reference AS reference, 'sale_invoice' AS source_type, id AS source_id,
                          CAST(total AS TEXT) AS amount, 'sale_invoice' AS description,
                          CAST(total AS TEXT) AS debit, '0' AS credit
                   FROM invoices WHERE customer_id=? AND type='sale' AND user_id=? AND deleted_at IS NULL""", (party_id, uid), 'date'),
                ("""SELECT date AS date, return_no AS reference, 'sales_return' AS source_type, id AS source_id,
                          CAST(total AS TEXT) AS amount, 'sales_return' AS description,
                          '0' AS debit, CAST(total AS TEXT) AS credit
                   FROM sales_returns WHERE customer_id=? AND user_id=? AND deleted_at IS NULL""", (party_id, uid), 'date'),
                ("""SELECT date AS date, reference AS reference, 'receipt_voucher' AS source_type, id AS source_id,
                          CAST(amount AS TEXT) AS amount, 'receipt_voucher' AS description,
                          '0' AS debit, CAST(amount AS TEXT) AS credit
                   FROM vouchers WHERE customer_id=? AND type='receipt' AND user_id=?""", (party_id, uid), 'date'),
            ]
            def apply_to_balance(balance, debit, credit):
                return balance + debit - credit
        else:
            parts = [
                ("""SELECT date AS date, reference AS reference, 'purchase_invoice' AS source_type, id AS source_id,
                          CAST(total AS TEXT) AS amount, 'purchase_invoice' AS description,
                          '0' AS debit, CAST(total AS TEXT) AS credit
                   FROM invoices WHERE supplier_id=? AND type='purchase' AND user_id=? AND deleted_at IS NULL""", (party_id, uid), 'date'),
                ("""SELECT date AS date, return_no AS reference, 'purchase_return' AS source_type, id AS source_id,
                          CAST(total AS TEXT) AS amount, 'purchase_return' AS description,
                          CAST(total AS TEXT) AS debit, '0' AS credit
                   FROM purchase_returns WHERE supplier_id=? AND user_id=? AND deleted_at IS NULL""", (party_id, uid), 'date'),
                ("""SELECT date AS date, reference AS reference, 'payment_voucher' AS source_type, id AS source_id,
                          CAST(amount AS TEXT) AS amount, 'payment_voucher' AS description,
                          CAST(amount AS TEXT) AS debit, '0' AS credit
                   FROM vouchers WHERE supplier_id=? AND type='payment' AND user_id=?""", (party_id, uid), 'date'),
            ]
            def apply_to_balance(balance, debit, credit):
                return balance + credit - debit

        queries = []
        params = []
        # Apply the end-date in SQL for efficiency.  Start-date is handled in
        # Python so we can compute a precise opening balance.
        for sql, p, dcol in parts:
            if end_date:
                sql += f" AND {dcol} <= ?"
                p = p + (end_date,)
            queries.append(sql)
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

    def get_customer_balances(self):
        db, uid = self._db_uid()
        if not uid:
            return []
        rows = db.execute("""
            SELECT id, name, phone, address, CAST(balance AS TEXT) AS balance
            FROM customers WHERE user_id=? ORDER BY name
        """, (uid,)).fetchall()
        return [dict(r) for r in rows]

    def get_supplier_balances(self):
        db, uid = self._db_uid()
        if not uid:
            return []
        rows = db.execute("""
            SELECT id, name, phone, address, CAST(balance AS TEXT) AS balance
            FROM suppliers WHERE user_id=? ORDER BY name
        """, (uid,)).fetchall()
        return [dict(r) for r in rows]

    def _aging(self, table, name_col='name', as_of_date=None):
        db, uid = self._db_uid()
        if not uid:
            return []
        as_of = self._parse_date(as_of_date) or date.today()
        rows = db.execute(f"SELECT id, {name_col} AS name, phone, CAST(balance AS TEXT) AS balance FROM {table} WHERE user_id=?", (uid,)).fetchall()
        result = []
        for row in rows:
            d = dict(row)
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
            result.append({**d, 'last_transaction_date': last_date or '', 'age_days': max(age, 0), **buckets})
        return result

    def _last_party_date(self, table, party_id, uid):
        if table == 'customers':
            sql = """
            SELECT MAX(dt) FROM (
              SELECT date AS dt FROM invoices WHERE customer_id=? AND type='sale' AND user_id=? AND deleted_at IS NULL
              UNION ALL SELECT date FROM sales_returns WHERE customer_id=? AND user_id=? AND deleted_at IS NULL
              UNION ALL SELECT date FROM vouchers WHERE customer_id=? AND type='receipt' AND user_id=?
            )
            """
        else:
            sql = """
            SELECT MAX(dt) FROM (
              SELECT date AS dt FROM invoices WHERE supplier_id=? AND type='purchase' AND user_id=? AND deleted_at IS NULL
              UNION ALL SELECT date FROM purchase_returns WHERE supplier_id=? AND user_id=? AND deleted_at IS NULL
              UNION ALL SELECT date FROM vouchers WHERE supplier_id=? AND type='payment' AND user_id=?
            )
            """
        return db_execute_scalar(sql, (party_id, uid, party_id, uid, party_id, uid))

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
