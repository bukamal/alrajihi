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


# Backward-compatible singleton for legacy imports.
expense_dao = ExpenseDAO()


# Keep legacy ``from database.dao import expense_dao`` imports returning the
# singleton object even after Python has attached the submodule object to the
# package during import.
try:
    import sys
    _dao_pkg = sys.modules.get("database.dao")
    if _dao_pkg is not None:
        setattr(_dao_pkg, "expense_dao", expense_dao)
except Exception:
    pass
