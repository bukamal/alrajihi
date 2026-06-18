# -*- coding: utf-8 -*-
"""Phase 210 guard: expense DAO export must resolve to singleton, not module."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
client = ROOT / 'alrajhi_client'

errors = []

def require(condition, message):
    if not condition:
        errors.append(message)

# The local expense gateway must import the concrete singleton directly.
expense_gateway = client / 'gateways/local/expense_gateway.py'
s = expense_gateway.read_text(encoding='utf-8')
require('from database.dao.expense_dao import expense_dao' in s,
        'LocalExpenseGateway must import expense_dao from database.dao.expense_dao directly')
require('from database import expense_dao' not in s,
        'LocalExpenseGateway must not import expense_dao through database package')
require('expense_dao.get_all' in s,
        'LocalExpenseGateway must still call the expense DAO singleton API')

# database public API must map the singleton directly to the submodule attribute,
# not to database.dao package attr that can be shadowed by a submodule object.
db_init = client / 'database/__init__.py'
s = db_init.read_text(encoding='utf-8')
require("'expense_dao': ('database.dao.expense_dao', 'expense_dao')" in s,
        'database.__init__ must export expense_dao directly from database.dao.expense_dao')
require("'expense_dao': ('database.dao', 'expense_dao')" not in s,
        'database.__init__ must not export expense_dao through database.dao package')

# The expense DAO module must define a singleton object with get_all-compatible class.
expense_dao = client / 'database/dao/expense_dao.py'
s = expense_dao.read_text(encoding='utf-8')
require(re.search(r'class\s+ExpenseDAO\b', s) is not None, 'ExpenseDAO class is missing')
require(re.search(r'def\s+get_all\s*\(', s) is not None, 'ExpenseDAO.get_all is missing')
require(re.search(r'^expense_dao\s*=\s*ExpenseDAO\s*\(\s*\)', s, re.M) is not None,
        'expense_dao singleton is missing')
require('setattr(_dao_pkg, "expense_dao", expense_dao)' in s,
        'expense_dao module must repair database.dao package shadowing')

# Reporting DAO had the same lazy package-shadow risk and must keep its singleton export stable.
reporting_dao = client / 'database/dao/reporting_dao.py'
s = reporting_dao.read_text(encoding='utf-8')
require(re.search(r'^reporting_dao\s*=\s*ReportingDAO\s*\(\s*\)', s, re.M) is not None,
        'reporting_dao singleton is missing')
require('setattr(_dao_pkg, "reporting_dao", reporting_dao)' in s,
        'reporting_dao module must repair database.dao package shadowing')

if errors:
    for e in errors:
        print(f'FAIL: {e}')
    raise SystemExit(1)
print('Phase 210 expense DAO export hotfix guard passed.')
