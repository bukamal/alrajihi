# -*- coding: utf-8 -*-
"""Deep regression test for manufacturing BOM recursion and item-unit ownership."""
from __future__ import annotations
import os, sys, shutil, types, json
from pathlib import Path
from decimal import Decimal
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get('ALRAJHI_MFG_DEEP_TEST_RUNTIME', '/tmp/alrajhi_manufacturing_deep_regression'))
if os.environ.get('ALRAJHI_TEST_RESET', '1') == '1':
    shutil.rmtree(RUNTIME, ignore_errors=True)
RUNTIME.mkdir(parents=True, exist_ok=True)
os.environ['ALRAJHI_DATA_DIR'] = str(RUNTIME)
os.environ['ALRAJHI_DB_PATH'] = str(RUNTIME / 'alrajhi_manufacturing_deep_regression.db')

try:
    import PyQt5  # noqa
except Exception:
    settings_store = {'network/mode': 'local'}
    class QSettings:
        def __init__(self,*a,**k): pass
        def value(self,k,d=None,*a,**kw): return settings_store.get(k,d)
        def setValue(self,k,v): settings_store[k]=v
    class QObject: pass
    class QTimer:
        @staticmethod
        def singleShot(*a, **k): pass
    def pyqtSignal(*a, **k):
        class Sig:
            def connect(self,*a,**k): pass
            def emit(self,*a,**k): pass
        return Sig()
    class Dummy:
        def __init__(self,*a,**k): pass
        def __getattr__(self,n):
            def f(*a,**k): return None
            return f
    qtcore=types.ModuleType('PyQt5.QtCore')
    for n,o in dict(QSettings=QSettings,QObject=QObject,QTimer=QTimer,pyqtSignal=pyqtSignal,Qt=Dummy,QSize=Dummy,QUrl=Dummy).items(): setattr(qtcore,n,o)
    qtwidgets=types.ModuleType('PyQt5.QtWidgets')
    for n in 'QApplication QWidget QMainWindow QDialog QMessageBox QVBoxLayout QHBoxLayout QLabel QPushButton QLineEdit QTableWidget QTableWidgetItem QComboBox QSpinBox QDoubleSpinBox QDateEdit QTextEdit QCheckBox QGroupBox QFormLayout QTabWidget QFileDialog QInputDialog QProgressDialog QFrame QSplitter QScrollArea'.split(): setattr(qtwidgets,n,Dummy)
    qtgui=types.ModuleType('PyQt5.QtGui')
    for n in 'QIcon QPixmap QFont QColor QDesktopServices QKeySequence'.split(): setattr(qtgui,n,Dummy)
    pyqt=types.ModuleType('PyQt5'); pyqt.QtCore=qtcore; pyqt.QtWidgets=qtwidgets; pyqt.QtGui=qtgui
    sys.modules.update({'PyQt5':pyqt,'PyQt5.QtCore':qtcore,'PyQt5.QtWidgets':qtwidgets,'PyQt5.QtGui':qtgui})

sys.path.insert(0, str(ROOT/'alrajhi_client'))
sys.path.insert(0, str(ROOT))

def dec(v): return Decimal(str(v))
def assert_dec(actual, expected, label):
    actual = dec(actual); expected = dec(expected)
    if abs(actual - expected) > dec('0.000001'):
        raise AssertionError(f'{label}: expected {expected}, got {actual}')

def main():
    from database.migrations import init_database
    from database.connection import DatabaseConnection
    from auth.session import UserSession
    init_database()
    UserSession.login({'id':'admin','username':'admin','role':'admin','branch_id':None})

    from core.services.entity_service import entity_service
    from core.services.product_service import product_service
    from core.services.invoice_service import invoice_service
    from core.services.warehouse_service import warehouse_service
    from core.services.manufacturing_service import manufacturing_service

    db = DatabaseConnection(); conn = db.get_connection()
    warehouse_service.bootstrap(); wh = warehouse_service.default_warehouse_id()
    supp = entity_service.add_supplier('MFG Deep Supplier','000','')
    cat = product_service.add_category({'name':'MFG Deep Category'})
    raw_a = product_service.add_item({'name':'MFG Deep Raw A','category_id':cat,'item_type':'مخزون','purchase_price':dec(2),'selling_price':0,'quantity':0,'unit':'pcs','average_cost':dec(2),'barcode':'MFG-DEEP-A','reorder_level':0})
    raw_b = product_service.add_item({'name':'MFG Deep Raw B','category_id':cat,'item_type':'مخزون','purchase_price':dec(5),'selling_price':0,'quantity':0,'unit':'pcs','average_cost':dec(5),'barcode':'MFG-DEEP-B','reorder_level':0})
    sub = product_service.add_item({'name':'MFG Deep Subassembly','category_id':cat,'item_type':'منتج نهائي','purchase_price':0,'selling_price':0,'quantity':0,'unit':'pcs','average_cost':0,'barcode':'MFG-DEEP-SUB','reorder_level':0})
    final = product_service.add_item({'name':'MFG Deep Final','category_id':cat,'item_type':'منتج نهائي','purchase_price':0,'selling_price':0,'quantity':0,'unit':'pcs','average_cost':0,'barcode':'MFG-DEEP-FIN','reorder_level':0})
    product_service.add_unit(raw_a, 'box', 12)
    product_service.add_unit(raw_b, 'pallet', 100)
    raw_a_box = conn.execute("SELECT id FROM item_units WHERE item_id=? AND unit_name='box'", (raw_a,)).fetchone()['id']
    raw_b_pallet = conn.execute("SELECT id FROM item_units WHERE item_id=? AND unit_name='pallet'", (raw_b,)).fetchone()['id']

    invoice_service.create({'type':'purchase','supplier_id':supp,'customer_id':None,'date':str(date(2026,6,15)),'reference':'MFG-DEEP-PUR','notes':'','total':dec(700),'paid_amount':0,'warehouse_id':wh,'branch_id':None,'cashbox_id':None,'bank_account_id':None,'payment_method':'cash','lines':[
        {'item_id':raw_a,'quantity':dec(100),'base_qty':dec(100),'unit_price':dec(2),'total':dec(200),'unit':'pcs','conversion_factor':1},
        {'item_id':raw_b,'quantity':dec(100),'base_qty':dec(100),'unit_price':dec(5),'total':dec(500),'unit':'pcs','conversion_factor':1},
    ]})

    invalid_rejected = False
    try:
        manufacturing_service.save_bom({'product_id': sub, 'quantity': dec(1), 'lines':[{'item_id': raw_a, 'quantity': dec(1), 'unit_id': raw_b_pallet, 'waste_percent': 0}]})
    except Exception as exc:
        invalid_rejected = 'الوحدة المحددة لا تتبع مادة المكون' in str(exc)
    if not invalid_rejected:
        raise AssertionError('unit ownership validation did not reject a unit_id from another item')

    # Sub BOM: 1 box Raw A produces 2 subassemblies.
    sub_bom = manufacturing_service.save_bom({'product_id': sub, 'quantity': dec(2), 'lines':[{'item_id': raw_a, 'quantity': dec(1), 'unit_id': raw_a_box, 'waste_percent': 0}]})
    # Final BOM: 1 subassembly + 0.5 Raw B produces 1 final. For 4 final:
    # Raw A = 1 box * 12 * (4 sub / 2) = 24 pcs; Raw B = 0.5 * 4 = 2 pcs.
    final_bom = manufacturing_service.save_bom({'product_id': final, 'quantity': dec(1), 'lines':[
        {'item_id': sub, 'quantity': dec(1), 'unit_id': None, 'waste_percent': 0},
        {'item_id': raw_b, 'quantity': dec('0.5'), 'unit_id': None, 'waste_percent': 0},
    ]})
    required = manufacturing_service.get_required_materials(final_bom, dec(4))
    by_item = {m['item_id']: m for m in required}
    assert raw_a in by_item, 'recursive get_required_materials missing exploded raw A'
    assert raw_b in by_item, 'recursive get_required_materials missing direct raw B'
    assert sub not in by_item, 'get_required_materials leaked intermediate subassembly instead of exploding it'
    assert_dec(by_item[raw_a]['required_qty'], '24', 'recursive raw A requirement')
    assert_dec(by_item[raw_b]['required_qty'], '2', 'direct raw B requirement')

    order_id = manufacturing_service.create_production_order(final, dec(4), 'deep recursion test', raw_warehouse_id=wh, output_warehouse_id=wh)
    reservations = {r['item_id']: r for r in manufacturing_service.get_reservations(order_id)}
    assert_dec(reservations[raw_a]['reserved_qty'], '24', 'reserved raw A after recursive expansion')
    assert_dec(reservations[raw_b]['reserved_qty'], '2', 'reserved raw B after recursive expansion')
    ok, msg = manufacturing_service.start_production(order_id); assert ok, msg
    ok, msg = manufacturing_service.consume_material(order_id, raw_a, dec(24), dec(2)); assert ok, msg
    ok, msg = manufacturing_service.consume_material(order_id, raw_b, dec(2), dec(5)); assert ok, msg
    ok, msg = manufacturing_service.complete_production(order_id, dec(4)); assert ok, msg
    out_cost = conn.execute('SELECT unit_cost FROM production_outputs WHERE order_id=?', (order_id,)).fetchone()['unit_cost']
    # total cost = 24*2 + 2*5 = 58, output 4 => 14.5
    assert_dec(out_cost, '14.5', 'recursive final unit cost')
    final_qty = conn.execute('SELECT quantity FROM items WHERE id=?', (final,)).fetchone()['quantity']
    raw_a_qty = conn.execute('SELECT quantity FROM items WHERE id=?', (raw_a,)).fetchone()['quantity']
    raw_b_qty = conn.execute('SELECT quantity FROM items WHERE id=?', (raw_b,)).fetchone()['quantity']
    assert_dec(final_qty, '4', 'final quantity after complete')
    assert_dec(raw_a_qty, '76', 'raw A quantity after complete')
    assert_dec(raw_b_qty, '98', 'raw B quantity after complete')

    result = {'invalid_unit_rejected': invalid_rejected, 'sub_bom': sub_bom, 'final_bom': final_bom, 'order_id': order_id, 'required': {str(k): str(v['required_qty']) for k,v in by_item.items()}, 'unit_cost': str(out_cost), 'after_complete': {'raw_a_qty': str(raw_a_qty), 'raw_b_qty': str(raw_b_qty), 'final_qty': str(final_qty)}}
    report = RUNTIME / 'MANUFACTURING_DEEP_REGRESSION_REPORT.json'
    report.write_text(json.dumps({'status':'PASS','result':result}, ensure_ascii=False, indent=2), encoding='utf-8')
    return result

if __name__ == '__main__':
    result = main()
    print('manufacturing_deep_regression_test: PASS')
    print(json.dumps(result, ensure_ascii=False, indent=2))
