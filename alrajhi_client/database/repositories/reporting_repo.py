# -*- coding: utf-8 -*-
from database.repositories.base_repo import BaseRepository
from decimal import Decimal
from typing import Dict, List

class ReportingRepository(BaseRepository):
    def get_summary_filtered(self, start_date: str = None, end_date: str = None) -> Dict:
        if self.db.is_remote():
            return self.db.get_rest_client().get_summary(start_date, end_date) if self.db.get_rest_client() else {}
        else:
            from auth.session import UserSession
            uid = UserSession.get_current_user_id()
            if not uid:
                return self._empty_summary()
            
            # إجمالي المبيعات (total من فواتير البيع)
            sales = self._safe_sum(
                "SELECT SUM(CAST(total AS REAL)) FROM invoices WHERE type='sale' AND user_id=? AND deleted_at IS NULL",
                (uid,), start_date, end_date, 'date'
            )

            # إجمالي المشتريات
            purchases = self._safe_sum(
                "SELECT SUM(CAST(total AS REAL)) FROM invoices WHERE type='purchase' AND user_id=? AND deleted_at IS NULL",
                (uid,), start_date, end_date, 'date'
            )

            # الحركة النقدية الفعلية: المقبوض والمدفوع من الفواتير والسندات والمرتجعات
            sale_paid = self._safe_sum(
                "SELECT SUM(CAST(paid AS REAL)) FROM invoices WHERE type='sale' AND user_id=? AND deleted_at IS NULL",
                (uid,), start_date, end_date, 'date'
            )
            purchase_paid = self._safe_sum(
                "SELECT SUM(CAST(paid AS REAL)) FROM invoices WHERE type='purchase' AND user_id=? AND deleted_at IS NULL",
                (uid,), start_date, end_date, 'date'
            )
            receipt_vouchers = self._safe_sum(
                "SELECT SUM(CAST(amount AS REAL)) FROM vouchers WHERE type='receipt' AND user_id=?",
                (uid,), start_date, end_date, 'date'
            )
            payment_vouchers = self._safe_sum(
                "SELECT SUM(CAST(amount AS REAL)) FROM vouchers WHERE type='payment' AND user_id=?",
                (uid,), start_date, end_date, 'date'
            )
            expense_vouchers = self._safe_sum(
                "SELECT SUM(CAST(amount AS REAL)) FROM vouchers WHERE type='expense' AND user_id=?",
                (uid,), start_date, end_date, 'date'
            )
            sales_return_refunds = self._safe_sum(
                "SELECT SUM(CAST(refund_amount AS REAL)) FROM sales_returns WHERE user_id=? AND deleted_at IS NULL",
                (uid,), start_date, end_date, 'date'
            )
            purchase_return_refunds = self._safe_sum(
                "SELECT SUM(CAST(refund_amount AS REAL)) FROM purchase_returns WHERE user_id=? AND deleted_at IS NULL",
                (uid,), start_date, end_date, 'date'
            )

            # تكلفة البضاعة المباعة (COGS) من cost_amount في سطور فواتير البيع
            cogs = self._safe_sum(
                """SELECT SUM(CAST(cost_amount AS REAL)) FROM invoice_lines il
                   JOIN invoices i ON il.invoice_id = i.id
                   WHERE i.type='sale' AND i.user_id=? AND i.deleted_at IS NULL""",
                (uid,), start_date, end_date, 'i.date'
            )
            
            # إجمالي المصروفات (من جدول expenses)
            expenses = self._safe_sum(
                "SELECT SUM(CAST(amount AS REAL)) FROM expenses WHERE user_id=?",
                (uid,), start_date, end_date, 'expense_date'
            )
            
            # رصيد الصندوق (آخر قيمة، بدون فلترة زمنية)
            cash_row = self._fetch_one("SELECT CAST(cash_balance AS REAL) as cash FROM users WHERE id=?", (uid,))
            cash = Decimal(str(cash_row['cash'])) if cash_row and cash_row['cash'] else Decimal('0')
            
            # الذمم المدينة (عملاء)
            receivables = self._safe_sum(
                "SELECT SUM(CAST(balance AS REAL)) FROM customers WHERE user_id=?",
                (uid,), None, None, None
            )
            
            # الذمم الدائنة (موردين)
            payables = self._safe_sum(
                "SELECT SUM(CAST(balance AS REAL)) FROM suppliers WHERE user_id=?",
                (uid,), None, None, None
            )
            
            # صافي الربح = المبيعات - COGS - المصروفات
            net_profit = sales - cogs - expenses
            
            return {
                'total_sales': sales,
                'cogs': cogs,
                'total_expenses': expenses,
                'net_profit': net_profit,
                'cash_balance': cash,
                'receivables': receivables,
                'payables': payables,
                'total_purchases': purchases,
                'total_incoming': sale_paid + receipt_vouchers + purchase_return_refunds,
                'total_outgoing': purchase_paid + payment_vouchers + expense_vouchers + sales_return_refunds,
                'cash_received': sale_paid + receipt_vouchers + purchase_return_refunds,
                'cash_paid': purchase_paid + payment_vouchers + expense_vouchers + sales_return_refunds,
                'cash_net_movement': (sale_paid + receipt_vouchers + purchase_return_refunds) - (purchase_paid + payment_vouchers + expense_vouchers + sales_return_refunds)
            }
    
    def _empty_summary(self) -> Dict:
        return {
            'total_sales': Decimal('0'),
            'cogs': Decimal('0'),
            'total_expenses': Decimal('0'),
            'net_profit': Decimal('0'),
            'cash_balance': Decimal('0'),
            'receivables': Decimal('0'),
            'payables': Decimal('0'),
            'total_purchases': Decimal('0'),
            'total_incoming': Decimal('0'),
            'total_outgoing': Decimal('0'),
            'cash_received': Decimal('0'),
            'cash_paid': Decimal('0'),
            'cash_net_movement': Decimal('0')
        }
    
    def _safe_sum(self, sql: str, params: tuple, start_date: str, end_date: str, date_column: str) -> Decimal:
        if start_date and end_date and date_column:
            # إضافة شرط التاريخ
            if 'WHERE' in sql.upper():
                sql += f" AND {date_column} BETWEEN ? AND ?"
            else:
                sql += f" WHERE {date_column} BETWEEN ? AND ?"
            params = params + (start_date, end_date)
        cur = self._execute(sql, params)
        val = cur.fetchone()[0]
        return Decimal(str(val)) if val is not None else Decimal('0')
    
    def get_income_statement_filtered(self, start_date: str = None, end_date: str = None) -> Dict:
        summary = self.get_summary_filtered(start_date, end_date)
        return {
            'income': [{'name': 'إجمالي الإيرادات', 'balance': summary['total_sales']}],
            'expenses': [{'name': 'تكلفة البضاعة المباعة', 'balance': summary['cogs']},
                         {'name': 'المصروفات التشغيلية', 'balance': summary['total_expenses']}],
            'total_income': summary['total_sales'],
            'total_expenses': summary['cogs'] + summary['total_expenses'],
            'net_profit': summary['net_profit']
        }
    
    def get_balance_sheet_filtered(self, start_date: str = None, end_date: str = None) -> Dict:
        summary = self.get_summary_filtered(start_date, end_date)
        assets = [
            {'name': 'الصندوق', 'debit': summary['cash_balance']},
            {'name': 'الذمم المدينة', 'debit': summary['receivables']}
        ]
        liabilities = [
            {'name': 'الذمم الدائنة', 'credit': summary['payables']}
        ]
        equity = [
            {'name': 'رأس المال', 'credit': summary['cash_balance'] + summary['receivables'] - summary['payables']}
        ]
        return {
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'total_assets': summary['cash_balance'] + summary['receivables'],
            'total_liabilities': summary['payables'],
            'total_equity': summary['cash_balance'] + summary['receivables'] - summary['payables']
        }


