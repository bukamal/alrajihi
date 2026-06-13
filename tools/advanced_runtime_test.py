# -*- coding: utf-8 -*-
"""Advanced headless runtime test for Alrajhi Phase 34+.

This script simulates several business days with local mode operations:
customers, suppliers, items, purchase/sale invoices, sales/purchase returns,
warehouse transfer/cancel, offline queue permanent failure handling, ledger
health/dual-read/readiness, gateway factories, and UI-service static command
compatibility.
"""
from __future__ import annotations
import os, sys, types, shutil, json, ast, traceback
from pathlib import Path
from decimal import Decimal
from datetime import date, timedelta

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get('ALRAJHI_TEST_RUNTIME', '/tmp/alrajhi_advanced_test_runtime'))
RESET = os.environ.get('ALRAJHI_TEST_RESET', '1') == '1'
if RESET:
    shutil.rmtree(RUNTIME, ignore_errors=True)
RUNTIME.mkdir(parents=True, exist_ok=True)
os.environ['ALRAJHI_DATA_DIR'] = str(RUNTIME)
os.environ['ALRAJHI_DB_PATH'] = str(RUNTIME / 'alrajhi_advanced_test.db')

# Headless PyQt5 fallback for service-layer testing environments.
try:
    import PyQt5  # noqa
except Exception:
    settings_store = {'network/mode': 'local'}
    class QSettings:
        def __init__(self, *a, **k): pass
        def value(self, key, default=None, *a, **k): return settings_store.get(key, default)
        def setValue(self, key, value): settings_store[key] = value
        def remove(self, key): settings_store.pop(key, None)
    class QObject: pass
    class QTimer:
        @staticmethod
        def singleShot(*a, **k): pass
    class Qt: pass
    class QSize:
        def __init__(self,*a): pass
    class QUrl: pass
    def pyqtSignal(*a, **k):
        class Sig:
            def connect(self,*a,**k): pass
            def emit(self,*a,**k): pass
        return Sig()
    class Dummy:
        def __init__(self,*a,**k): pass
        def __getattr__(self, name):
            def f(*a, **k): return None
            return f
    qtcore = types.ModuleType('PyQt5.QtCore')
    for name, obj in dict(QSettings=QSettings, QObject=QObject, QTimer=QTimer, Qt=Qt, QSize=QSize, QUrl=QUrl, pyqtSignal=pyqtSignal).items(): setattr(qtcore, name, obj)
    qtwidgets = types.ModuleType('PyQt5.QtWidgets')
    for n in 'QApplication QWidget QMainWindow QDialog QMessageBox QVBoxLayout QHBoxLayout QLabel QPushButton QLineEdit QTableWidget QTableWidgetItem QComboBox QSpinBox QDoubleSpinBox QDateEdit QTextEdit QCheckBox QGroupBox QFormLayout QTabWidget QFileDialog QInputDialog QProgressDialog QFrame QSplitter QScrollArea'.split(): setattr(qtwidgets, n, Dummy)
    qtgui = types.ModuleType('PyQt5.QtGui')
    for n in 'QIcon QPixmap QFont QColor QDesktopServices'.split(): setattr(qtgui, n, Dummy)
    pyqt = types.ModuleType('PyQt5'); pyqt.QtCore=qtcore; pyqt.QtWidgets=qtwidgets; pyqt.QtGui=qtgui
    sys.modules.update({'PyQt5':pyqt,'PyQt5.QtCore':qtcore,'PyQt5.QtWidgets':qtwidgets,'PyQt5.QtGui':qtgui})

sys.path.insert(0, str(ROOT / 'alrajhi_client'))
sys.path.insert(0, str(ROOT))

results = []
def record(name, status, detail=None):
    results.append({'name': name, 'status': status, 'detail': detail})
    print(f"{status}: {name}" + (f" -> {detail}" if detail is not None else ''))

def check(name, fn):
    try:
        record(name, 'PASS', fn())
    except Exception as exc:
        record(name, 'FAIL', repr(exc))
        traceback.print_exc()

def dec(v): return Decimal(str(v))

def init_database_and_session():
    from database.migrations import init_database
    from auth.session import UserSession
    init_database()
    UserSession.login({'id':'admin','username':'admin','role':'admin','branch_id':None})
    return os.environ['ALRAJHI_DB_PATH']

check('init_database_and_session', init_database_and_session)

def import_all_services():
    imported = []
    for p in sorted((ROOT/'alrajhi_client/core/services').glob('*service.py')):
        __import__('core.services.' + p.stem)
        imported.append(p.stem)
    return {'count': len(imported), 'services': imported}
check('import_all_core_services', import_all_services)

def gateway_factory_check():
    factories = []
    for p in sorted((ROOT/'alrajhi_client/gateways').glob('*gateway.py')):
        m = __import__('gateways.' + p.stem, fromlist=['*'])
        for name, obj in vars(m).items():
            if name.startswith('create_') and callable(obj):
                instance = obj()
                gateways = instance if isinstance(instance, tuple) else (instance,)
                for g in gateways:
                    if not hasattr(g, 'is_remote'):
                        raise AssertionError(f'{type(g).__name__} lacks is_remote()')
                    g.is_remote()
                factories.append(name)
    return {'count': len(factories), 'factories': factories}
check('gateway_factories_instantiate_and_is_remote', gateway_factory_check)


def static_ui_service_compatibility():
    forbidden = []
    for base in [ROOT/'alrajhi_client/views', ROOT/'alrajhi_client/core/services']:
        for p in base.rglob('*.py'):
            s = p.read_text(encoding='utf-8')
            if 'from database.dao' in s or 'from database.repositories' in s or 'sqlite3.connect' in s:
                forbidden.append(str(p.relative_to(ROOT)))
    service_methods = {}
    for p in (ROOT/'alrajhi_client/core/services').glob('*service.py'):
        tree = ast.parse(p.read_text(encoding='utf-8'))
        for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
            singleton = p.stem
            service_methods[singleton] = {m.name for m in cls.body if isinstance(m, ast.FunctionDef) and not m.name.startswith('_')}
    unknown_calls = []
    for p in (ROOT/'alrajhi_client/views').rglob('*.py'):
        tree = ast.parse(p.read_text(encoding='utf-8'))
        imports = {}
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith('core.services.'):
                for alias in n.names:
                    imports[alias.asname or alias.name] = n.module.split('.')[-1]
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name):
                var = n.func.value.id
                if var in imports and var in service_methods and n.func.attr not in service_methods[var]:
                    unknown_calls.append((str(p.relative_to(ROOT)), var, n.func.attr))
    if forbidden or unknown_calls:
        raise AssertionError({'forbidden': forbidden, 'unknown_calls': unknown_calls[:30]})
    return {'forbidden': 0, 'unknown_service_calls': 0}
check('static_ui_service_command_compatibility', static_ui_service_compatibility)


def advanced_business_days():
    from database.connection import DatabaseConnection
    from core.services.entity_service import entity_service
    from core.services.product_service import product_service
    from core.services.invoice_service import invoice_service
    from core.services.warehouse_service import warehouse_service
    from core.services.sales_return_service import sales_return_service
    from core.services.purchase_return_service import purchase_return_service
    from core.services.inventory_service import inventory_service
    db = DatabaseConnection(); conn = db.get_connection()
    warehouse_service.bootstrap()
    wh1 = warehouse_service.default_warehouse_id()
    wh2 = warehouse_service.add_warehouse({'name':'WH-Test-2','code':'WH2','location':'test','notes':'advanced test','is_active':1})
    cust = entity_service.add_customer('ADV Customer','111','addr')
    supp = entity_service.add_supplier('ADV Supplier','222','addr')
    cat = product_service.add_category({'name':'ADV Category'})
    item = product_service.add_item({'name':'ADV Item','category_id':cat,'item_type':'مخزون','purchase_price':dec(10),'selling_price':dec(15),'quantity':dec(0),'unit':'pcs','average_cost':dec(10),'barcode':'ADV001','reorder_level':dec(1)})
    def payload(typ, qty, price, ref, d):
        return {'type':typ,'customer_id':cust if typ=='sale' else None,'supplier_id':supp if typ=='purchase' else None,'date':d.isoformat(),'reference':ref,'notes':'advanced runtime','total':dec(qty)*dec(price),'paid_amount':dec(0),'warehouse_id':wh1,'branch_id':None,'cashbox_id':None,'bank_account_id':None,'payment_method':'cash','lines':[{'item_id':item,'quantity':dec(qty),'base_qty':dec(qty),'unit_price':dec(price),'total':dec(qty)*dec(price),'unit':'pcs','conversion_factor':dec(1)}]}
    day0 = date(2026,6,13)
    purchase_id = invoice_service.create(payload('purchase', 20, 10, 'ADV-P-001', day0))
    sale_id = invoice_service.create(payload('sale', 5, 15, 'ADV-S-001', day0+timedelta(days=1)))
    sale_lines = sales_return_service.invoice_returnable_lines(sale_id)
    sr_id = sales_return_service.create_return({'original_invoice_id': sale_id, 'date': str(day0+timedelta(days=2)), 'warehouse_id': wh1, 'refund_amount':'0', 'lines':[{'original_invoice_line_id': sale_lines[0]['id'], 'quantity':'1'}]})
    purchase_lines = purchase_return_service.invoice_returnable_lines(purchase_id)
    pr_id = purchase_return_service.create_return({'original_invoice_id': purchase_id, 'date': str(day0+timedelta(days=3)), 'warehouse_id': wh1, 'refund_amount':'0', 'lines':[{'original_invoice_line_id': purchase_lines[0]['id'], 'quantity':'2'}]})
    transfer_id = warehouse_service.create_transfer({'item_id':item, 'from_warehouse_id':wh1, 'to_warehouse_id':wh2, 'quantity':'3', 'notes':'advanced transfer'})
    warehouse_service.cancel_transfer(transfer_id)
    # Edit and delete guarded flows: edit sale from 5 to 4, then do not delete because it has return; test guard.
    try:
        invoice_service.update(sale_id, payload('sale', 4, 15, 'ADV-S-001-EDIT', day0+timedelta(days=4)))
        update_guard = 'updated'
    except Exception as exc:
        update_guard = 'blocked:' + str(exc)[:80]
    try:
        invoice_service.delete(sale_id)
        delete_guard = 'deleted_unexpected'
    except Exception as exc:
        delete_guard = 'blocked:' + str(exc)[:80]
    item_row = conn.execute('SELECT quantity, average_cost FROM items WHERE id=?', (item,)).fetchone()
    inv_movs = [dict(r) for r in conn.execute('SELECT movement_type, quantity, reference_id FROM inventory_movements WHERE item_id=? ORDER BY id', (item,)).fetchall()]
    wh_mov_count = conn.execute('SELECT COUNT(*) FROM warehouse_movements WHERE item_id=?', (item,)).fetchone()[0]
    ledger = [dict(r) for r in conn.execute('SELECT movement_type, direction, quantity, reference_type, reference_id FROM inventory_ledger WHERE item_id=? ORDER BY id', (item,)).fetchall()]
    dual = inventory_service.ledger_dual_read() if hasattr(inventory_service, 'ledger_dual_read') else {}
    readiness = inventory_service.ledger_readiness() if hasattr(inventory_service, 'ledger_readiness') else {}
    controlled = inventory_service.ledger_controlled_read(item_id=item, warehouse_id=wh1) if hasattr(inventory_service, 'ledger_controlled_read') else {}
    return {
        'ids': {'item':item,'purchase':purchase_id,'sale':sale_id,'sales_return':sr_id,'purchase_return':pr_id,'transfer':transfer_id,'wh1':wh1,'wh2':wh2},
        'item_quantity_after_flow': item_row['quantity'],
        'inventory_movements': inv_movs,
        'warehouse_movement_count': wh_mov_count,
        'ledger_count': len(ledger),
        'ledger_sample': ledger[:20],
        'invoice_update_guard': update_guard,
        'invoice_delete_guard': delete_guard,
        'dual_read_keys': sorted(list(dual.keys())) if isinstance(dual, dict) else type(dual).__name__,
        'readiness_keys': sorted(list(readiness.keys())) if isinstance(readiness, dict) else type(readiness).__name__,
        'controlled_read': controlled,
    }
check('advanced_business_flow_multi_day_simulation', advanced_business_days)


def offline_queue_flow():
    from database.connection import offline_queue
    q1 = offline_queue.add_request('/api/invoices', 'POST', {'reference':'OFF-ADV-1','type':'sale','lines':[{'item_id':1,'quantity':'1'}]}, error='simulated network error')
    pending_before = offline_queue.count_pending()
    offline_queue.mark_attempt(q1, 'connection refused')
    offline_queue.mark_failed(q1, 'API error 400 validation')
    row = [r for r in offline_queue.get_recent_requests(10) if r['id'] == q1][0]
    if row['status'] != 'failed' or offline_queue.count_pending() != pending_before - 1:
        raise AssertionError(row)
    return {'queued_id': q1, 'status': row['status'], 'pending_after': offline_queue.count_pending()}
check('offline_queue_permanent_failure_and_no_infinite_retry', offline_queue_flow)

failed = [r for r in results if r['status'] != 'PASS']
summary = {'passed': len(results)-len(failed), 'failed': len(failed), 'results': results}
report_path = RUNTIME / 'ADVANCED_RUNTIME_TEST_REPORT.json'
report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print('\nSUMMARY', json.dumps({'passed': summary['passed'], 'failed': summary['failed'], 'report': str(report_path)}, ensure_ascii=False))
if failed:
    raise SystemExit(1)
