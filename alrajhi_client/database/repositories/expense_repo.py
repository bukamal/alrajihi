# -*- coding: utf-8 -*-
from database.repositories.base_repo import BaseRepository
from currency import currency
from decimal import Decimal
from typing import List, Dict

class ExpenseRepository(BaseRepository):
    def get_all(self, convert_to_display: bool = True) -> List[Dict]:
        """جلب جميع الحركات من نوع expense أو receipt (الإيرادات) من جدول vouchers"""
        if self.db.is_remote():
            return self.db.get_rest_client().get_expenses()
        else:
            rows = self.db.execute("SELECT * FROM vouchers WHERE type IN ('expense', 'receipt') ORDER BY id DESC").fetchall()
            expenses = []
            for row in rows:
                e = dict(row)
                # تحويل إلى هيكل expenses القديم للتوافق
                e['amount_original'] = e['amount']
                e['currency_original'] = e['original_currency']
                e['amount_display'] = e['amount']
                e['type'] = 'outgoing' if e['type'] == 'expense' else 'incoming'
                e['expense_date'] = e['date']
                e['company_name'] = e.get('description', 'مصروف عام')
                expenses.append(e)
            return expenses

    def get_by_company(self, company_name: str, convert_to_display: bool = True) -> List[Dict]:
        all_expenses = self.get_all(convert_to_display=False)
        filtered = [e for e in all_expenses if e['company_name'] == company_name]
        if convert_to_display:
            for e in filtered:
                e['amount_display'] = e.get('amount_original', e['amount'])
                e['currency_display'] = e.get('currency_original', e.get('currency', 'SAR'))
        return filtered

    def add(self, company_name: str, amount: float, type_val: str, date: str,
            notes: str, currency_code: str, user_id: int) -> int:
        """إضافة مصروف أو إيراد عن طريق إنشاء سند من النوع expense أو receipt"""
        voucher_type = 'expense' if type_val == 'outgoing' else 'receipt'
        rate_to_usd = currency.get_rate_to_usd(currency_code)
        if currency_code == 'USD':
            amount_usd = amount
        else:
            amount_usd = amount / rate_to_usd

        data = {
            'type': voucher_type,
            'amount': amount_usd,
            'date': date,
            'description': notes or company_name,
            'reference': '',
            'customer_id': None,
            'supplier_id': None,
            'invoice_id': None,
            'exchange_rate_to_usd': rate_to_usd,
            'original_currency': currency_code
        }
        return self.db.add_voucher(data)

    def update(self, expense_id: int, company_name: str, amount: float, type_val: str,
               date: str, notes: str, currency_code: str, user_id: int):
        # نحتاج أولاً إلى معرف السند المرتبط (expense_id هو id في جدول expenses القديم، لكننا لم نعد نستخدمه)
        # بدلاً من ذلك، نفترض أن expense_id هو id في vouchers (لأننا دمجنا)
        # في الواجهة، سنقوم بتعديل expense مباشرة من vouchers. لكن للتوافق، سنقوم بحذف وإعادة إنشاء
        voucher = self.db.get_voucher_by_id(expense_id)
        if voucher:
            self.db.delete_voucher(expense_id)
            # إعادة إنشاء بنفس البيانات المعدلة
            self.add(company_name, amount, type_val, date, notes, currency_code, user_id)
        else:
            raise Exception("لم يتم العثور على السند المرتبط")

    def delete(self, expense_id: int, user_id: int = None):
        # حذف السند المرتبط
        self.db.delete_voucher(expense_id)

    def get_summary(self, convert_to_display: bool = True) -> Dict:
        expenses = self.get_all(convert_to_display=False)
        total_in = sum(e['amount'] for e in expenses if e['type'] == 'incoming')
        total_out = sum(e['amount'] for e in expenses if e['type'] == 'outgoing')
        companies_count = len(set(e['company_name'] for e in expenses))
        return {
            'total_incoming': total_in,
            'total_outgoing': total_out,
            'net': total_in - total_out,
            'companies_count': companies_count
        }


