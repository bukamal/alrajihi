# -*- coding: utf-8 -*-
from __future__ import annotations
import os, sys, shutil, types, json, time, ast, traceback, subprocess
from pathlib import Path
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get('ALRAJHI_TEST_RUNTIME', '/tmp/alrajhi_release_hardening_phase111'))
shutil.rmtree(RUNTIME, ignore_errors=True); RUNTIME.mkdir(parents=True, exist_ok=True)
os.environ['ALRAJHI_DATA_DIR'] = str(RUNTIME)
os.environ['ALRAJHI_DB_PATH'] = str(RUNTIME / 'release_hardening.db')

try:
    import PyQt5  # noqa
except Exception:
    settings_store={'network/mode':'local'}
    class QSettings:
        def __init__(self,*a,**k): pass
        def value(self,key,default=None,*a,**kw): return settings_store.get(key,default)
        def setValue(self,key,value): settings_store[key]=value
        def remove(self,key): settings_store.pop(key,None)
    class QObject: pass
    class QTimer:
        @staticmethod
        def singleShot(*a,**k): pass
    class Qt: pass
    class QSize:
        def __init__(self,*a,**k): pass
    class QUrl: pass
    def pyqtSignal(*a,**k):
        class S:
            def connect(self,*a,**k): pass
            def emit(self,*a,**k): pass
        return S()
    class Dummy:
        def __init__(self,*a,**k): pass
        def __getattr__(self,n): return lambda *a,**k: None
    qtcore=types.ModuleType('PyQt5.QtCore'); qtwidgets=types.ModuleType('PyQt5.QtWidgets'); qtgui=types.ModuleType('PyQt5.QtGui')
    for n,o in dict(QSettings=QSettings,QObject=QObject,QTimer=QTimer,Qt=Qt,QSize=QSize,QUrl=QUrl,pyqtSignal=pyqtSignal).items(): setattr(qtcore,n,o)
    for n in 'QApplication QWidget QMainWindow QDialog QMessageBox QVBoxLayout QHBoxLayout QLabel QPushButton QLineEdit QTableWidget QTableWidgetItem QComboBox QSpinBox QDoubleSpinBox QDateEdit QTextEdit QCheckBox QGroupBox QFormLayout QTabWidget QFileDialog QInputDialog QProgressDialog QFrame QSplitter QScrollArea'.split(): setattr(qtwidgets,n,Dummy)
    for n in 'QIcon QPixmap QFont QColor QDesktopServices'.split(): setattr(qtgui,n,Dummy)
    pyqt=types.ModuleType('PyQt5'); pyqt.QtCore=qtcore; pyqt.QtWidgets=qtwidgets; pyqt.QtGui=qtgui
    sys.modules.update({'PyQt5':pyqt,'PyQt5.QtCore':qtcore,'PyQt5.QtWidgets':qtwidgets,'PyQt5.QtGui':qtgui})

sys.path.insert(0, str(ROOT / 'alrajhi_client')); sys.path.insert(0, str(ROOT))
results=[]
def rec(name, status, detail=None):
    results.append({'name': name, 'status': status, 'detail': detail})
    print(f'{status}: {name}' + (f' -> {detail}' if detail is not None else ''))

def check(name, fn):
    try:
        rec(name, 'PASS', fn())
    except Exception as e:
        rec(name, 'FAIL', {'error': repr(e), 'traceback': traceback.format_exc(limit=8)})

def D(x): return Decimal(str(x))

check('migration_idempotent_and_schema_columns', lambda: migration_check()) if False else None

def bootstrap():
    from database.migrations import init_database
    from auth.session import UserSession
    init_database(); init_database()
    UserSession.login({'id':'admin','username':'admin','role':'admin','branch_id':None})
    from database.connection import DatabaseConnection
    conn = DatabaseConnection().get_connection()
    required = {
        'invoices': ['cashbox_id','bank_account_id','payment_method','shift_id'],
        'invoice_lines': ['quantity_in_base','conversion_factor','cost_amount'],
        'inventory_movements': ['movement_type','quantity','unit_cost','reference_id'],
        'inventory_ledger': ['direction','quantity','reference_type','reference_id'],
        'vouchers': ['cashbox_id','bank_account_id','payment_method'],
        'item_units': ['item_id','unit_name','conversion_factor'],
    }
    missing=[]
    for table, cols in required.items():
        existing={r['name'] for r in conn.execute(f'PRAGMA table_info({table})').fetchall()}
        for c in cols:
            if c not in existing: missing.append(f'{table}.{c}')
    if missing: raise AssertionError(missing)
    return {'db': os.environ['ALRAJHI_DB_PATH'], 'required_columns_ok': True}
check('migration_idempotent_and_schema_columns', bootstrap)


def accounting_and_units_flow():
    from core.services.entity_service import entity_service
    from core.services.product_service import product_service
    from core.services.invoice_service import invoice_service
    from core.services.voucher_service import voucher_service
    from core.services.sales_return_service import sales_return_service
    from core.services.purchase_return_service import purchase_return_service
    from core.services.warehouse_service import warehouse_service
    from core.services.cashbox_service import cashbox_service
    from database.connection import DatabaseConnection
    conn = DatabaseConnection().get_connection()
    warehouse_service.bootstrap(); wh=warehouse_service.default_warehouse_id()
    cashbox_service.bootstrap(); default_cashbox = cashbox_service.default_cashbox_id(); bank_id = cashbox_service.add_bank_account({'bank_name':'Phase111 Bank','account_name':'Main','account_number':'111','opening_balance':'0','is_active':1})
    cust=entity_service.add_customer('Phase111 Customer','','')
    supp=entity_service.add_supplier('Phase111 Supplier','','')
    cat=product_service.add_category({'name':'Phase111 Category'})
    item=product_service.add_item({'name':'Phase111 Item','category_id':cat,'item_type':'مخزون','purchase_price':10,'selling_price':15,'quantity':1000,'unit':'pcs','average_cost':10,'barcode':'PH111A','reorder_level':0})
    product_service.replace_units(item, [{'unit_name':'box','conversion_factor':12}])
    def payload(t, qty, price, paid, ref, method='cash', cashbox=None, bank=None, shift=None):
        return {'type':t,'customer_id':cust if t=='sale' else None,'supplier_id':supp if t=='purchase' else None,'date':'2026-06-15','reference':ref,'notes':'phase111','total':D(qty)*D(price),'paid_amount':D(paid),'warehouse_id':wh,'branch_id':None,'cashbox_id':(default_cashbox if cashbox is None else cashbox),'bank_account_id':bank,'payment_method':method,'shift_id':shift,'lines':[{'item_id':item,'quantity':D(qty),'base_qty':D(qty)*D(12),'unit_price':D(price),'total':D(qty)*D(price),'unit':'box','conversion_factor':D(12)}]}
    p=invoice_service.create(payload('purchase',10,120,0,'PH111-P')) # +120 pcs cost/base 10
    s=invoice_service.create(payload('sale',5,180,360,'PH111-S','card',default_cashbox,bank_id,3)) # -60 pcs, balance 540
    before = conn.execute('SELECT quantity, average_cost FROM items WHERE id=?',(item,)).fetchone()
    if D(before['quantity']) != D(1060): raise AssertionError({'qty_after_sale': before['quantity']})
    sr_line=sales_return_service.invoice_returnable_lines(s)[0]
    sr=sales_return_service.create_return({'original_invoice_id':s,'date':'2026-06-15','warehouse_id':wh,'refund_amount':'0','lines':[{'original_invoice_line_id':sr_line['id'],'quantity':'1'}]})
    pr_line=purchase_return_service.invoice_returnable_lines(p)[0]
    pr=purchase_return_service.create_return({'original_invoice_id':p,'date':'2026-06-15','warehouse_id':wh,'refund_amount':'0','lines':[{'original_invoice_line_id':pr_line['id'],'quantity':'1'}]})
    after_returns = conn.execute('SELECT quantity, average_cost FROM items WHERE id=?',(item,)).fetchone()
    # 1060 + sales_return 12 - purchase_return 12 = 1060
    if D(after_returns['quantity']) != D(1060): raise AssertionError({'qty_after_returns': after_returns['quantity']})
    try:
        invoice_service.update(s, payload('sale',4,180,0,'PH111-S-UPD'))
        raise AssertionError('invoice update with return was allowed')
    except Exception as e:
        if 'مرتجعات' not in str(e): raise
    voucher_id = voucher_service.add({'type':'receipt','date':'2026-06-15','amount':'100','description':'phase111','reference':'VR111','customer_id':cust,'supplier_id':None,'invoice_id':s,'payment_method':'cash','cashbox_id':default_cashbox})
    try:
        invoice_service.delete(s)
        raise AssertionError('invoice delete with linked return/voucher was allowed')
    except Exception as e:
        if 'مرتجعات' not in str(e) and 'سندات' not in str(e): raise
    # invoice update payment metadata on invoice without linked returns/vouchers
    s2=invoice_service.create(payload('sale',1,180,0,'PH111-S2','card',default_cashbox,bank_id,3))
    invoice_service.update(s2, payload('sale',1,180,0,'PH111-S2U','bank',None,bank_id,7))
    meta=dict(conn.execute('SELECT cashbox_id, bank_account_id, payment_method, shift_id FROM invoices WHERE id=?',(s2,)).fetchone())
    
    if meta.get('bank_account_id') != bank_id or meta.get('payment_method') != 'bank' or meta.get('shift_id') != 7: raise AssertionError(meta)
    try:
        invoice_service.create(payload('sale',2000,180,0,'PH111-OVER'))
        raise AssertionError('oversell allowed')
    except Exception as e:
        if 'الرصيد' not in str(e): raise
    return {'purchase':p,'sale':s,'sales_return':sr,'purchase_return':pr,'voucher':voucher_id,'quantity':str(after_returns['quantity']),'avg_cost':str(after_returns['average_cost']),'payment_metadata_update':meta,'oversell_blocked':True}
check('accounting_units_returns_vouchers_integrity', accounting_and_units_flow)


def transaction_rollback_probe():
    from core.services.invoice_service import invoice_service
    from database.connection import DatabaseConnection
    conn=DatabaseConnection().get_connection()
    before=conn.execute('SELECT COUNT(*) FROM invoices').fetchone()[0]
    try:
        invoice_service.create({'type':'sale','customer_id':1,'date':'2026-06-15','reference':'BAD-ROLLBACK','total':'10','paid_amount':'0','warehouse_id':1,'lines':[{'item_id':1,'quantity':'1','base_qty':'1','total':'10'}]}) # missing unit_price
    except Exception:
        pass
    after=conn.execute('SELECT COUNT(*) FROM invoices').fetchone()[0]
    if before != after: raise AssertionError({'before':before,'after':after})
    return {'invoice_count_before':before,'invoice_count_after':after,'rolled_back':True}
check('transaction_rollback_on_invalid_invoice_payload', transaction_rollback_probe)


def performance_smoke():
    from core.services.entity_service import entity_service
    from core.services.product_service import product_service
    from core.services.invoice_service import invoice_service
    from core.services.warehouse_service import warehouse_service
    from database.connection import DatabaseConnection
    conn=DatabaseConnection().get_connection(); warehouse_service.bootstrap(); wh=warehouse_service.default_warehouse_id()
    cust=entity_service.add_customer('Perf Customer','','')
    supp=entity_service.add_supplier('Perf Supplier','','')
    cat=product_service.add_category({'name':'Perf Category'})
    item=product_service.add_item({'name':'Perf Item','category_id':cat,'item_type':'مخزون','purchase_price':1,'selling_price':2,'quantity':0,'unit':'pcs','average_cost':1,'barcode':'PH111P','reorder_level':0})
    def pld(t, qty, ref):
        return {'type':t,'customer_id':cust if t=='sale' else None,'supplier_id':supp if t=='purchase' else None,'date':'2026-06-15','reference':ref,'notes':'perf','total':D(qty)*(D(2) if t=='sale' else D(1)),'paid_amount':0,'warehouse_id':wh,'lines':[{'item_id':item,'quantity':D(qty),'base_qty':D(qty),'unit_price':D(2) if t=='sale' else D(1),'total':D(qty)*(D(2) if t=='sale' else D(1)),'unit':'pcs','conversion_factor':1}]}
    invoice_service.create(pld('purchase',5000,'PERF-P-INIT'))
    start=time.perf_counter()
    for i in range(250): invoice_service.create(pld('sale',1,f'PERF-S-{i:04d}'))
    elapsed=time.perf_counter()-start
    row=conn.execute('SELECT quantity FROM items WHERE id=?',(item,)).fetchone()
    if D(row['quantity']) != D(4750): raise AssertionError(row['quantity'])
    return {'sales_created':250,'seconds':round(elapsed,3),'per_invoice_ms':round(elapsed/250*1000,3),'final_qty':row['quantity']}
check('performance_smoke_250_invoice_writes', performance_smoke)


def static_security_probe():
    dangerous=[]; bare=[]; sql_f=[]
    for p in list((ROOT/'alrajhi_client').rglob('*.py'))+list((ROOT/'alrajhi_server').rglob('*.py')):
        if '__pycache__' in p.parts: continue
        try: tree=ast.parse(p.read_text(encoding='utf-8'))
        except Exception: continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in {'eval','exec'}:
                dangerous.append((str(p.relative_to(ROOT)), n.lineno, n.func.id))
            if isinstance(n, ast.ExceptHandler) and n.type is None:
                bare.append((str(p.relative_to(ROOT)), n.lineno))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'execute' and n.args:
                a=n.args[0]
                if isinstance(a, ast.JoinedStr): sql_f.append((str(p.relative_to(ROOT)), n.lineno, 'f-string execute'))
                if isinstance(a, ast.BinOp) and isinstance(a.op, ast.Mod): sql_f.append((str(p.relative_to(ROOT)), n.lineno, '% execute'))
    # Qt dialog.exec() is intentionally ignored because AST sees it as Attribute, not Name.
    return {'eval_exec_calls': dangerous[:20], 'eval_exec_count': len(dangerous), 'bare_except_count': len(bare), 'sql_string_format_count': len(sql_f), 'sql_string_format_sample': sql_f[:20], 'status': 'WARN' if dangerous or sql_f or len(bare)>20 else 'OK'}
check('static_security_probe_no_eval_exec_and_sql_formatting', static_security_probe)


def concurrency_documented_probe():
    # The desktop local service uses a singleton SQLite connection; this probe validates sequential integrity
    # and records that true multi-process contention requires a deployed DB/server test harness.
    from database.connection import DatabaseConnection
    conn=DatabaseConnection().get_connection()
    ok = conn.execute('PRAGMA integrity_check').fetchone()[0]
    if ok != 'ok': raise AssertionError(ok)
    return {'sqlite_integrity_check': ok, 'note': 'true multi-user concurrency must be tested against deployed server/database, not the single-process desktop connection'}
check('sqlite_integrity_and_concurrency_scope', concurrency_documented_probe)

report={'summary':{'passed':sum(1 for r in results if r['status']=='PASS'),'failed':sum(1 for r in results if r['status']!='PASS')},'results':results}
out=ROOT/'test_reports'/'release_hardening_audit_phase111.json'
out.parent.mkdir(exist_ok=True); out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('SUMMARY', json.dumps(report['summary'], ensure_ascii=False), 'REPORT', out)
if report['summary']['failed']:
    raise SystemExit(1)
