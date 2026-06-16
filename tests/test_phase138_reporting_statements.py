from decimal import Decimal
import sqlite3
import sys
import types
import importlib.util
from pathlib import Path

# Load reporting_dao.py without importing alrajhi_client.database.__init__, which
# requires PyQt5 through the runtime DatabaseConnection path. The tested method
# is pure SQL once _db_uid is overridden below.
repo_mod = types.ModuleType('database.repositories.reporting_repo')
class ReportingRepository:  # pragma: no cover - constructor is bypassed
    pass
repo_mod.ReportingRepository = ReportingRepository
sys.modules.setdefault('database', types.ModuleType('database'))
sys.modules.setdefault('database.repositories', types.ModuleType('database.repositories'))
sys.modules['database.repositories.reporting_repo'] = repo_mod

path = Path(__file__).resolve().parents[1] / 'alrajhi_client' / 'database' / 'dao' / 'reporting_dao.py'
spec = importlib.util.spec_from_file_location('phase138_reporting_dao', path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ReportingDAO = mod.ReportingDAO

class TestReportingDAO(ReportingDAO):
    def __init__(self, db, uid=1):
        self._db = db
        self._uid = uid
    def _db_uid(self):
        return self._db, self._uid

def make_db():
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    db.executescript('''
    CREATE TABLE invoices (id INTEGER, date TEXT, reference TEXT, total TEXT, type TEXT, customer_id INTEGER, supplier_id INTEGER, user_id INTEGER, deleted_at TEXT);
    CREATE TABLE sales_returns (id INTEGER, date TEXT, return_no TEXT, total TEXT, customer_id INTEGER, user_id INTEGER, deleted_at TEXT);
    CREATE TABLE purchase_returns (id INTEGER, date TEXT, return_no TEXT, total TEXT, supplier_id INTEGER, user_id INTEGER, deleted_at TEXT);
    CREATE TABLE vouchers (id INTEGER, date TEXT, reference TEXT, amount TEXT, type TEXT, customer_id INTEGER, supplier_id INTEGER, user_id INTEGER);
    ''')
    return db

def test_customer_statement_has_opening_balance_and_running_total():
    db = make_db()
    db.execute("INSERT INTO invoices VALUES (1,'2026-01-01','S-1','100','sale',10,NULL,1,NULL)")
    db.execute("INSERT INTO vouchers VALUES (1,'2026-01-05','R-1','40','receipt',10,NULL,1)")
    db.execute("INSERT INTO invoices VALUES (2,'2026-02-01','S-2','30','sale',10,NULL,1,NULL)")
    rows = TestReportingDAO(db).get_customer_statement(10, '2026-02-01', '2026-02-28')
    assert rows[0]['source_type'] == 'opening_balance'
    assert rows[0]['balance'] == Decimal('60')
    assert rows[1]['reference'] == 'S-2'
    assert rows[1]['balance'] == Decimal('90')

def test_supplier_statement_has_opening_balance_and_running_total():
    db = make_db()
    db.execute("INSERT INTO invoices VALUES (1,'2026-01-01','P-1','200','purchase',NULL,20,1,NULL)")
    db.execute("INSERT INTO vouchers VALUES (1,'2026-01-05','PV-1','50','payment',NULL,20,1)")
    db.execute("INSERT INTO purchase_returns VALUES (1,'2026-02-02','PR-1','30',20,1,NULL)")
    rows = TestReportingDAO(db).get_supplier_statement(20, '2026-02-01', '2026-02-28')
    assert rows[0]['source_type'] == 'opening_balance'
    assert rows[0]['balance'] == Decimal('150')
    assert rows[1]['reference'] == 'PR-1'
    assert rows[1]['balance'] == Decimal('120')
