# -*- coding: utf-8 -*-
from database.repositories.expense_repo import ExpenseRepository
from decimal import Decimal

class ExpenseDAO:
    def __init__(self):
        self.repo = ExpenseRepository()
    
    def get_all(self, search=None):
        expenses = self.repo.get_all()
        if search:
            expenses = [e for e in expenses if search in e.get('description', '').lower()]
        return expenses
    
    def add(self, amount, date, description):
        from currency import currency
        from auth.session import UserSession
        user = UserSession.get_current()
        return self.repo.add(
            company_name='مصروف عام',
            amount=amount,
            type_val='outgoing',
            date=date,
            notes=description,
            currency_code=currency.get_display_currency(),
            user_id=user['id'] if user else None
        )
    
    def delete(self, expense_id):
        self.repo.delete(expense_id)


